import asyncio
import json
import os
import tempfile
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, SessionLocal, engine, session
from app.media import media_url, verify_media_request
from app.models import AuditLog, Camera, DetectionEvent, InferenceJob, ModelVersion, ProcessedVideo, Tracklet, TrafficAggregate
from app.jobs import video_jobs
from app.hls import HlsManager
from app.queue import enqueue_job
from app.schemas import (
    CameraIn,
    CameraUpdate,
    EventIn,
    InferenceFrameRequest,
    InferenceFrameResponse,
    InferenceVideoRequest,
    InferenceVideoResponse,
    ModelIn,
    VideoJobResponse,
)
from app.security import rate_limit, require
from app.storage import stream_file
from app.services import ModelManager, _annotate, audit, ingest_event, process_live_frame, process_uploaded_video

PROCESSED_VIDEO_DIR = Path(os.getenv('PROCESSED_VIDEO_DIR', 'processed-videos')).resolve()
PROCESSED_VIDEO_DIR.mkdir(parents=True, exist_ok=True)
HLS = HlsManager(PROCESSED_VIDEO_DIR)


def _run_hls_detection(source: str, camera_id: str, stop_event: Any) -> None:
    """Analyze HLS source frames in memory and persist events only.

    FFmpeg creates the browser playlist; this independent low-rate reader is
    deliberately never written to disk, so live sessions cannot create video
    artifacts while still producing DetectionEvent rows.
    """
    import cv2
    from datetime import datetime, timezone

    db = SessionLocal()
    capture = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
    frame_index = 0
    try:
        while not stop_event.is_set() and capture.isOpened():
            processed = _capture_and_process(capture, ModelManager.get_detector(), 640)
            if processed:
                _, detections = processed
                if detections:
                    now = datetime.now(timezone.utc)
                    for detection in detections:
                        db.add(DetectionEvent(
                            id=f'evt_{uuid4().hex[:16]}', camera_id=camera_id,
                            occurred_at=now, payload={
                                'event_type': 'live_detection', 'frame_index': frame_index,
                                'transport': 'hls', **detection,
                            },
                        ))
                    db.commit()
                frame_index += 1
            stop_event.wait(0.5)
    except Exception:
        db.rollback()
    finally:
        capture.release()
        db.close()


def _capture_and_process(capture: Any, detector: Any, max_width: int) -> tuple[bytes, list[dict[str, Any]]] | None:
    """Read one RTSP frame, run detection, annotate, and return JPEG bytes.

    Runs in a worker thread so the event loop stays free between frames.
    Tracking is intentionally disabled here (predict, not track/persist) because
    the detector is a shared singleton; this keeps the live preview CPU-safe and
    free of cross-stream state corruption.
    """
    import cv2

    ok, frame = capture.read()
    if not ok:
        return None
    height, width = frame.shape[:2]
    if width > max_width:
        ratio = max_width / width
        frame = cv2.resize(frame, (max_width, max(1, int(height * ratio))))
    with ModelManager.inference_lock():
        results = detector(frame, conf=0.25, iou=0.45, verbose=False)[0]
    boxes = results.boxes
    detections: list[dict[str, Any]] = []
    if boxes is None or len(boxes) == 0:
        annotated = frame
    else:
        coords = boxes.xyxy.cpu().tolist()
        confs = boxes.conf.cpu().tolist()
        classes = boxes.cls.int().cpu().tolist()
        names = results.names
        class_names = [str(names.get(class_id, class_id)) for class_id in classes]
        detections = [
            {'box': box, 'confidence': float(conf), 'class_id': int(class_id), 'class_name': class_name}
            for box, conf, class_id, class_name in zip(coords, confs, classes, class_names)
        ]
        annotated = _annotate(frame, coords, [-1] * len(coords), confs, class_names)
    ret, buf = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 75])
    return (buf.tobytes(), detections) if ret else None


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    # Backward-compatible additive migration for existing SQLite development DBs.
    if engine.dialect.name == 'sqlite':
        tables = set(inspect(engine).get_table_names())
        if 'cameras' in tables:
            columns = {column['name'] for column in inspect(engine).get_columns('cameras')}
            if 'stream_url' not in columns:
                with engine.begin() as connection:
                    connection.execute(text('ALTER TABLE cameras ADD COLUMN stream_url VARCHAR'))
        if 'detection_events' in tables:
            columns = {column['name'] for column in inspect(engine).get_columns('detection_events')}
            if 'plate_text' not in columns:
                with engine.begin() as connection:
                    connection.execute(text('ALTER TABLE detection_events ADD COLUMN plate_text VARCHAR'))
        if 'inference_jobs' in tables:
            columns = {column['name'] for column in inspect(engine).get_columns('inference_jobs')}
            if 'payload' not in columns:
                with engine.begin() as connection:
                    connection.execute(text('ALTER TABLE inference_jobs ADD COLUMN payload JSON'))
    # Register processed video files created before the archive table existed so
    # the dashboard can browse them immediately after an upgrade.
    db = SessionLocal()
    try:
        for stale in db.scalars(select(ProcessedVideo)).all():
            if not (PROCESSED_VIDEO_DIR / stale.file_name).is_file():
                db.delete(stale)
        db.commit()
        known = set(db.scalars(select(ProcessedVideo.file_name)).all())
        for path in PROCESSED_VIDEO_DIR.iterdir():
            if not path.is_file() or path.suffix.lower() not in {'.webm', '.mp4'}:
                continue
            if path.name in known:
                continue
            db.add(ProcessedVideo(
                id=f'vid_{uuid4().hex[:16]}', file_name=path.name,
                original_name=path.stem, video_id=path.stem, camera_id=None,
                created_at=datetime.fromtimestamp(path.stat().st_mtime),
                frames_processed=0, duration_seconds=0.0, file_size=path.stat().st_size,
                model_version=None, plate_count=0, source='legacy',
            ))
        db.commit()
    finally:
        db.close()
    yield

app = FastAPI(
    title='YemenVision Traffic Platform',
    version='0.2.0',
    openapi_url='/api/v1/openapi.json',
    docs_url='/api/v1/docs',
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.get('/health')
@app.get('/api/v1/health')
def health():
    """Liveness endpoint for local development, Docker and reverse proxies."""
    import shutil
    return {
        'status': 'ok', 'service': 'traffic-platform', 'version': '0.2.0',
        'ffmpeg_available': shutil.which('ffmpeg') is not None,
        **ModelManager.accelerator_info(),
    }


@app.get('/api/v1/media/{name}')
def media(name: str, exp: int, sig: str):
    """Serve a processed video through a short-lived HMAC-signed URL."""
    if not verify_media_request(name, exp, sig):
        raise HTTPException(403, 'Invalid or expired media signature')
    path = (PROCESSED_VIDEO_DIR / name).resolve()
    if path.parent != PROCESSED_VIDEO_DIR or not path.is_file():
        remote = stream_file(f'processed/{Path(name).name}')
        if remote is None:
            raise HTTPException(404, 'Media not found')
        return StreamingResponse(remote.iter_chunks(), media_type='video/webm', headers={'Cache-Control': 'private, max-age=300'})
    media_type = 'video/webm' if path.suffix.lower() == '.webm' else 'video/mp4'
    return FileResponse(path, media_type=media_type, headers={'Cache-Control': 'private, max-age=300'})


def _video_out(row: ProcessedVideo) -> dict:
    return {
        'id': row.id, 'file_name': row.file_name, 'original_name': row.original_name,
        'video_id': row.video_id, 'camera_id': row.camera_id,
        'created_at': row.created_at, 'frames_processed': row.frames_processed,
        'duration_seconds': row.duration_seconds, 'file_size': row.file_size,
        'model_version': row.model_version, 'plate_count': row.plate_count,
        'source': row.source, 'video_url': media_url(row.file_name),
    }


@app.post('/api/v1/cameras', status_code=201, dependencies=[Depends(rate_limit)])
def create_camera(body: CameraIn, user=Depends(require('admin', 'operator')), db: Session = Depends(session)):
    if db.get(Camera, body.id):
        raise HTTPException(409, 'Camera already exists')
    db.add(Camera(**body.model_dump()))
    audit(db, user['subject'], 'camera.create', f'cameras/{body.id}', {})
    db.commit()
    return body

@app.get('/api/v1/cameras', dependencies=[Depends(rate_limit)])
def cameras(user=Depends(require('admin', 'operator', 'analyst')), db: Session = Depends(session)):
    return list(db.scalars(select(Camera).order_by(Camera.id)).all())

@app.put('/api/v1/cameras/{camera_id}', dependencies=[Depends(rate_limit)])
def update_camera(camera_id: str, body: CameraUpdate, user=Depends(require('admin', 'operator')), db: Session = Depends(session)):
    camera = db.get(Camera, camera_id)
    if not camera:
        raise HTTPException(404, 'Camera not found')
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(camera, key, value)
    audit(db, user['subject'], 'camera.update', f'cameras/{camera_id}', body.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(camera)
    return camera

@app.delete('/api/v1/cameras/{camera_id}', dependencies=[Depends(rate_limit)])
def delete_camera(camera_id: str, user=Depends(require('admin', 'operator')), db: Session = Depends(session)):
    camera = db.get(Camera, camera_id)
    if not camera:
        raise HTTPException(404, 'Camera not found')
    historical = {
        'events': len(db.scalars(select(DetectionEvent.id).where(DetectionEvent.camera_id == camera_id)).all()),
        'tracklets': len(db.scalars(select(Tracklet.id).where(Tracklet.camera_id == camera_id)).all()),
    }
    db.delete(camera)
    audit(db, user['subject'], 'camera.delete', f'cameras/{camera_id}', historical)
    db.commit()
    return {'status': 'deleted', 'camera_id': camera_id, 'historical_rows_kept': historical}

@app.post('/api/v1/events', status_code=202, dependencies=[Depends(rate_limit)])
def events(body: EventIn, user=Depends(require('admin', 'operator')), db: Session = Depends(session)):
    if not db.get(Camera, body.camera_id):
        db.add(Camera(id=body.camera_id, zone="auto-zone", direction="two-way", active=True))
        db.commit()
    row, created = ingest_event(db, body, user['subject'])
    return {'id': row.id, 'status': 'accepted' if created else 'duplicate_ignored'}

@app.get('/api/v1/events', dependencies=[Depends(rate_limit)])
def list_events(
    camera_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
    user=Depends(require('admin', 'operator', 'analyst')),
    db: Session = Depends(session)
):
    if not 1 <= limit <= 1000:
        raise HTTPException(422, 'limit must be 1..1000')
    q = select(DetectionEvent).order_by(DetectionEvent.occurred_at.desc()).offset(offset).limit(limit)
    if camera_id:
        q = q.where(DetectionEvent.camera_id == camera_id)
    return list(db.scalars(q).all())

@app.get('/api/v1/tracklets', dependencies=[Depends(rate_limit)])
def list_tracklets(
    camera_id: str | None = None,
    video_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
    user=Depends(require('admin', 'operator', 'analyst')),
    db: Session = Depends(session)
):
    if not 1 <= limit <= 1000:
        raise HTTPException(422, 'limit must be 1..1000')
    q = select(Tracklet).order_by(Tracklet.start_time.desc()).offset(offset).limit(limit)
    if camera_id:
        q = q.where(Tracklet.camera_id == camera_id)
    if video_id:
        q = q.where(Tracklet.video_id == video_id)
    return list(db.scalars(q).all())

@app.get('/api/v1/videos', dependencies=[Depends(rate_limit)])
def list_videos(
    camera_id: str | None = None,
    search: str | None = None,
    limit: int = 24,
    offset: int = 0,
    user=Depends(require('admin', 'operator', 'analyst')),
    db: Session = Depends(session)
):
    """Browse processed videos with short-lived signed playback URLs."""
    if not 1 <= limit <= 100:
        raise HTTPException(422, 'limit must be 1..100')
    q = select(ProcessedVideo)
    if camera_id:
        q = q.where(ProcessedVideo.camera_id == camera_id)
    if search:
        term = f'%{search.strip()}%'
        q = q.where(
            ProcessedVideo.original_name.like(term)
            | ProcessedVideo.video_id.like(term)
            | ProcessedVideo.file_name.like(term)
        )
    rows = db.scalars(q.order_by(ProcessedVideo.created_at.desc()).offset(offset).limit(limit)).all()
    return [_video_out(row) for row in rows if (PROCESSED_VIDEO_DIR / row.file_name).is_file()]

@app.get('/api/v1/videos/{video_id}', dependencies=[Depends(rate_limit)])
def get_video(video_id: str, user=Depends(require('admin', 'operator', 'analyst')), db: Session = Depends(session)):
    row = db.get(ProcessedVideo, video_id)
    if not row or not (PROCESSED_VIDEO_DIR / row.file_name).is_file():
        raise HTTPException(404, 'Video not found')
    return _video_out(row)

@app.delete('/api/v1/videos/{video_id}', dependencies=[Depends(rate_limit)])
def delete_video(video_id: str, user=Depends(require('admin', 'operator')), db: Session = Depends(session)):
    row = db.get(ProcessedVideo, video_id)
    if not row:
        raise HTTPException(404, 'Video not found')
    path = (PROCESSED_VIDEO_DIR / row.file_name).resolve()
    if path.parent == PROCESSED_VIDEO_DIR:
        path.unlink(missing_ok=True)
    audit(db, user['subject'], 'video.delete', f'videos/{row.video_id}', {'file_name': row.file_name})
    db.delete(row)
    db.commit()
    return {'status': 'deleted', 'video_id': video_id}


@app.get('/api/v1/live/stream', dependencies=[Depends(rate_limit)])
def live_stream(
    url: str = Query(..., description='RTSP/HTTP stream URL'),
    camera_id: str | None = Query(None, description='Optional camera row to validate/link'),
    max_fps: float = Query(5.0, ge=0.5, le=30, description='Maximum processed frames per second'),
    max_width: int = Query(640, ge=160, le=1280, description='Max inference width (CPU safety)'),
    persist_results: bool = Query(True, description='Persist detections without saving video'),
    api_key: str | None = Query(None, description='Fallback API key for  tag access'),
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(session),
):
    """MJPEG live preview for an RTSP/HTTP stream with on-the-fly detection.

    The stream is served as ``multipart/x-mixed-replace`` so a plain
    ``<img src>`` can display it. Each viewer opens its own capture; keep
    ``max_fps`` low on weak machines.
    """
    key = x_api_key or api_key
    if not key:
        raise HTTPException(401, 'Missing API key')
    try:
        users = json.loads(settings.api_keys_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(503, 'API key configuration is invalid') from exc
    identity = users.get(key)
    if not isinstance(identity, dict) or not identity.get('subject') or not isinstance(identity.get('roles'), list):
        raise HTTPException(401, 'Invalid API key')
    if camera_id:
        camera = db.get(Camera, camera_id)
        if not camera:
            raise HTTPException(404, 'Camera not found')
    try:
        detector = ModelManager.get_detector()
    except Exception as exc:
        raise HTTPException(503, f'Detector unavailable: {exc}')

    async def generate() -> Any:
        import cv2
        from datetime import datetime, timezone

        result_db = SessionLocal() if persist_results and camera_id else None
        frame_index = 0

        # Create the RTSP capture in a worker thread with a hard timeout so an
        # unreachable stream cannot block the event loop forever.
        def create_capture() -> Any:
            cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
            try:
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            except Exception:
                pass
            return cap

        try:
            capture = await asyncio.wait_for(
                asyncio.to_thread(create_capture),
                timeout=10.0,
            )
        except asyncio.TimeoutError:
            yield b'--frame\r\nContent-Type: text/plain\r\n\r\nRTSP stream connection timed out\r\n'
            return
        except Exception as exc:
            yield f'--frame\r\nContent-Type: text/plain\r\n\r\nCannot open RTSP stream: {exc}\r\n'.encode()
            return

        try:
            if not capture.isOpened():
                yield b'--frame\r\nContent-Type: text/plain\r\n\r\nCannot open RTSP stream\r\n'
                return

            min_interval = 1.0 / max_fps
            last_yield = 0.0
            while True:
                now = time.monotonic()
                if now - last_yield < min_interval:
                    await asyncio.sleep(0.01)
                    continue
                try:
                    processed = await asyncio.wait_for(
                        asyncio.to_thread(_capture_and_process, capture, detector, max_width),
                        timeout=8.0,
                    )
                except asyncio.TimeoutError:
                    yield b'--frame\r\nContent-Type: text/plain\r\n\r\nFrame read timed out\r\n'
                    continue
                last_yield = now
                if processed is None:
                    await asyncio.sleep(0.05)
                    continue
                jpeg, detections = processed
                if result_db and detections:
                    now = datetime.now(timezone.utc)
                    for detection in detections:
                        result_db.add(DetectionEvent(
                            id=f'evt_{uuid4().hex[:16]}', camera_id=camera_id,
                            occurred_at=now, payload={
                                'event_type': 'live_detection', 'frame_index': frame_index,
                                **detection,
                            },
                        ))
                    result_db.commit()
                frame_index += 1
                yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg + b'\r\n'
        except asyncio.CancelledError:
            pass
        finally:
            capture.release()
            if result_db:
                result_db.close()

    return StreamingResponse(generate(), media_type='multipart/x-mixed-replace; boundary=--frame')


@app.post('/api/v1/live/hls/start', dependencies=[Depends(rate_limit)])
def start_hls_stream(
    url: str = Query(..., description='RTSP/HTTP source URL'),
    camera_id: str | None = Query(None, description='Registered camera for live result persistence'),
    db: Session = Depends(session),
    user=Depends(require('admin', 'operator')),
):
    if not url.lower().startswith(('rtsp://', 'rtsps://', 'http://', 'https://')):
        raise HTTPException(422, 'Unsupported live source URL')
    if camera_id and not db.get(Camera, camera_id):
        raise HTTPException(404, 'Camera not found')
    try:
        stream = HLS.start(url, camera_id=camera_id, detection_callback=_run_hls_detection)
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    return {
        'session_id': stream.id,
        'playlist_url': f'/api/v1/live/hls/{stream.id}/index.m3u8?token={stream.token}',
        'expires_in': 900,
    }


@app.get('/api/v1/live/hls/{session_id}/index.m3u8')
def hls_playlist(session_id: str, token: str = Query(...)):
    stream = HLS.get(session_id, token)
    if stream is None:
        raise HTTPException(404, 'HLS session not found or expired')
    playlist = stream.directory / 'index.m3u8'
    if not playlist.is_file():
        raise HTTPException(425, 'HLS playlist is still starting')
    # FFmpeg emits bare segment names. Add the session token so the browser
    # can fetch every segment through the protected API route.
    lines = []
    for line in playlist.read_text(encoding='utf-8').splitlines():
        if line and not line.startswith('#') and '?' not in line:
            line = f'{line}?token={token}'
        lines.append(line)
    return PlainTextResponse('\n'.join(lines) + '\n', media_type='application/vnd.apple.mpegurl', headers={'Cache-Control': 'no-store'})


@app.get('/api/v1/live/hls/{session_id}/{segment}')
def hls_segment(session_id: str, segment: str, token: str = Query(...)):
    stream = HLS.get(session_id, token)
    if stream is None or Path(segment).name != segment:
        raise HTTPException(404, 'HLS session not found')
    path = (stream.directory / segment).resolve()
    if path.parent != stream.directory or not path.is_file():
        raise HTTPException(404, 'HLS segment not found')
    return FileResponse(path, media_type='video/mp2t', headers={'Cache-Control': 'no-store'})


@app.delete('/api/v1/live/hls/{session_id}')
def stop_hls_stream(session_id: str, token: str = Query(...), user=Depends(require('admin', 'operator'))):
    if not HLS.stop(session_id, token):
        raise HTTPException(404, 'HLS session not found')
    return {'status': 'stopped', 'session_id': session_id}

@app.get('/api/v1/plates', dependencies=[Depends(rate_limit)])
def list_plates(
    camera_id: str | None = None,
    plate: str | None = None,
    limit: int = 100,
    offset: int = 0,
    user=Depends(require('admin', 'operator', 'analyst')),
    db: Session = Depends(session)
):
    """Plate readings extracted during video inference, newest first."""
    if not 1 <= limit <= 1000:
        raise HTTPException(422, 'limit must be 1..1000')
    q = select(DetectionEvent).where(DetectionEvent.plate_text.is_not(None))
    if camera_id:
        q = q.where(DetectionEvent.camera_id == camera_id)
    if plate:
        q = q.where(DetectionEvent.plate_text.like(f'%{plate.strip()}%'))
    rows = db.scalars(q.order_by(DetectionEvent.occurred_at.desc()).offset(offset).limit(limit)).all()
    return [{
        'id': row.id, 'camera_id': row.camera_id, 'occurred_at': row.occurred_at,
        'plate_text': row.plate_text, 'video_id': row.payload.get('video_id'),
        'frame_index': row.payload.get('frame_index'),
        'track_id': row.payload.get('track_id'),
        'class_name': row.payload.get('class_name'),
        'confidence': row.payload.get('plate_confidence', row.payload.get('confidence')),
        'status': row.payload.get('plate_status'),
    } for row in rows]

@app.post('/api/v1/inference/video', status_code=410, dependencies=[Depends(rate_limit)])
def infer_video(
    body: InferenceVideoRequest,
    user=Depends(require('admin', 'operator')),
    db: Session = Depends(session)
):
    """Deprecated: server-side path inference was previously simulated.

    Use POST /api/v1/inference/upload with the actual video bytes. This
    endpoint is kept only to return an actionable error instead of fabricated
    results.
    """
    raise HTTPException(
        410,
        'Server-path inference is disabled. Upload the video to /api/v1/inference/upload instead.',
    )

@app.post('/api/v1/inference/upload', status_code=200, dependencies=[Depends(rate_limit)])
async def upload_video(
    request: Request,
    camera_id: str,
    max_frames: int = Query(default=300, ge=1, le=3600),
    async_processing: bool = Query(default=False, description='Queue the job and return immediately'),
    user=Depends(require('admin', 'operator')),
    db: Session = Depends(session),
):
    """Accept the actual video bytes (not a browser-local path).

    ``max_frames`` limits how many frames are decoded and processed; the
    default of 300 keeps the previous behaviour.
    """
    content_type = request.headers.get('content-type', '')
    if not content_type.startswith('video/') and content_type != 'application/octet-stream':
        raise HTTPException(415, 'Upload a video file')
    max_bytes = settings.max_upload_bytes
    original_name = unquote(request.headers.get('x-file-name', 'uploaded-video.mp4'))
    # Treat the header as a filename, not a path; never use client path components.
    original_name = Path(original_name.replace('\\', '/')).name
    suffix = Path(original_name).suffix.lower()
    if suffix not in {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.mpeg', '.mpg'}:
        raise HTTPException(415, 'Unsupported video extension')
    temp_path = None
    total = 0
    try:
        staging_dir = PROCESSED_VIDEO_DIR / '.incoming'
        staging_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            prefix='yv-video-', suffix=suffix, dir=staging_dir, delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            async for chunk in request.stream():
                total += len(chunk)
                if total > max_bytes:
                    raise HTTPException(413, f'Video exceeds {max_bytes} byte limit')
                handle.write(chunk)
        if total == 0:
            raise HTTPException(400, 'Uploaded video is empty')
        if not db.get(Camera, camera_id):
            db.add(Camera(id=camera_id, zone='video-upload', direction='two-way', active=True))
            db.commit()
        body = InferenceVideoRequest(
            camera_id=camera_id, video_path=str(temp_path),
            max_frames=max_frames, original_name=original_name,
        )
        if async_processing:
            # The worker owns cleanup of the temporary input and its DB session.
            queued_path = temp_path
            temp_path = None
            job_id = f'job_{uuid4().hex[:16]}'
            now = datetime.now(timezone.utc)
            db.add(InferenceJob(
                id=job_id, status='queued', progress=0, camera_id=camera_id,
                original_name=original_name,
                payload={'video_path': str(queued_path), 'max_frames': max_frames, 'actor': user['subject']},
                created_at=now, updated_at=now,
            ))
            db.commit()

            if settings.queue_backend == 'redis' and enqueue_job(job_id):
                return {
                    'id': job_id, 'status': 'queued', 'progress': 0,
                    'camera_id': camera_id, 'original_name': original_name,
                    'result': None, 'error': None,
                    'created_at': now.isoformat(), 'updated_at': now.isoformat(),
                }

            def run_job(_job_id: str) -> dict:
                worker_db = SessionLocal()
                output_path = PROCESSED_VIDEO_DIR / f'{uuid4().hex}.webm'
                try:
                    def report_progress(frames: int, total: int | None) -> None:
                        progress = round((frames / total) * 100) if total else 1
                        video_jobs.update_progress(_job_id, progress)
                        row = worker_db.get(InferenceJob, _job_id)
                        if row:
                            row.status = 'running'
                            row.progress = max(1, min(99, progress))
                            row.updated_at = datetime.now(timezone.utc)
                            worker_db.commit()

                    result = process_uploaded_video(
                        worker_db, body, user['subject'], output_path,
                        progress_callback=report_progress,
                    )
                    payload = result.model_dump(mode='json')
                    row = worker_db.get(InferenceJob, _job_id)
                    if row:
                        row.status, row.progress, row.result = 'completed', 100, payload
                        row.updated_at = datetime.now(timezone.utc)
                        worker_db.commit()
                    return payload
                except Exception:
                    output_path.unlink(missing_ok=True)
                    worker_db.rollback()
                    row = worker_db.get(InferenceJob, _job_id)
                    if row:
                        row.status, row.progress, row.error = 'failed', 100, 'Video processing failed'
                        row.updated_at = datetime.now(timezone.utc)
                        worker_db.commit()
                    raise
                finally:
                    worker_db.close()
                    queued_path.unlink(missing_ok=True)

            job = video_jobs.submit(camera_id, original_name, run_job)
            return job.public()
        output_path = PROCESSED_VIDEO_DIR / f'{uuid4().hex}.webm'
        try:
            result = process_uploaded_video(db, body, user['subject'], output_path)
        except ValueError as exc:
            output_path.unlink(missing_ok=True)
            db.rollback()
            raise HTTPException(422, str(exc)) from exc
        except RuntimeError as exc:
            output_path.unlink(missing_ok=True)
            db.rollback()
            raise HTTPException(503, str(exc)) from exc
        except Exception:
            output_path.unlink(missing_ok=True)
            db.rollback()
            raise
        return result
    finally:
        if temp_path:
            temp_path.unlink(missing_ok=True)


@app.get('/api/v1/inference/jobs/{job_id}', response_model=VideoJobResponse, dependencies=[Depends(rate_limit)])
def get_inference_job(
    job_id: str,
    user=Depends(require('admin', 'operator', 'analyst')),
):
    job = video_jobs.get(job_id)
    if job is not None:
        return job.public()
    db = SessionLocal()
    try:
        row = db.get(InferenceJob, job_id)
        if row is None:
            raise HTTPException(404, 'Inference job not found')
        return {
            'id': row.id, 'status': row.status, 'progress': row.progress,
            'camera_id': row.camera_id, 'original_name': row.original_name,
            'result': row.result, 'error': row.error,
            'created_at': row.created_at.isoformat(), 'updated_at': row.updated_at.isoformat(),
        }
    finally:
        db.close()

@app.post('/api/v1/inference/frame', response_model=InferenceFrameResponse, status_code=200, dependencies=[Depends(rate_limit)])
def infer_frame(
    body: InferenceFrameRequest,
    user=Depends(require('admin', 'operator')),
    db: Session = Depends(session)
):
    if not db.get(Camera, body.camera_id):
        db.add(Camera(id=body.camera_id, zone="live-stream", direction="two-way", active=True))
        db.commit()
    return process_live_frame(db, body, user['subject'])

@app.get('/api/v1/traffic', dependencies=[Depends(rate_limit)])
def traffic(camera_id: str | None = None, limit: int = 100, user=Depends(require('admin', 'operator', 'analyst')), db: Session = Depends(session)):
    q = select(TrafficAggregate).order_by(TrafficAggregate.bucket_start.desc()).limit(min(limit, 1000))
    if camera_id:
        q = q.where(TrafficAggregate.camera_id == camera_id)
    return list(db.scalars(q).all())

@app.get('/api/v1/models', dependencies=[Depends(rate_limit)])
def list_models(user=Depends(require('admin', 'operator', 'analyst'))):
    """Report the real model registry state (including revoked/corrupt files)."""
    from yemenvision.registry import ModelRegistry
    registry = ModelRegistry(settings.models_dir, trusted_models_only=settings.trusted_models_only)
    return {
        'models_dir': str(registry.models_dir),
        'records': [record.as_dict() for record in registry.discover()],
    }


@app.post('/api/v1/models', status_code=201, dependencies=[Depends(rate_limit)])
def model(body: ModelIn, user=Depends(require('admin')), db: Session = Depends(session)):
    if db.get(ModelVersion, body.id):
        raise HTTPException(409, 'Model id exists')
    db.add(ModelVersion(**body.model_dump()))
    audit(db, user['subject'], 'model.register', f'models/{body.id}', {})
    db.commit()
    return body

@app.get('/api/v1/audit', dependencies=[Depends(rate_limit)])
def audit_log(limit: int = 100, user=Depends(require('admin')), db: Session = Depends(session)):
    return list(db.scalars(select(AuditLog).order_by(AuditLog.occurred_at.desc()).limit(min(limit, 1000))).all())
