import os
import tempfile
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, SessionLocal, engine, session
from app.media import media_url, verify_media_request
from app.models import AuditLog, Camera, DetectionEvent, ModelVersion, ProcessedVideo, Tracklet, TrafficAggregate
from app.schemas import (
    CameraIn,
    CameraUpdate,
    EventIn,
    InferenceFrameRequest,
    InferenceFrameResponse,
    InferenceVideoRequest,
    InferenceVideoResponse,
    ModelIn,
)
from app.security import rate_limit, require
from app.services import audit, ingest_event, process_live_frame, process_uploaded_video

PROCESSED_VIDEO_DIR = Path(os.getenv('PROCESSED_VIDEO_DIR', 'processed-videos')).resolve()
PROCESSED_VIDEO_DIR.mkdir(parents=True, exist_ok=True)

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
def health():
    return {'status': 'ok', 'service': 'traffic-platform', 'version': '0.2.0'}


@app.get('/api/v1/media/{name}')
def media(name: str, exp: int, sig: str):
    """Serve a processed video through a short-lived HMAC-signed URL."""
    if not verify_media_request(name, exp, sig):
        raise HTTPException(403, 'Invalid or expired media signature')
    path = (PROCESSED_VIDEO_DIR / name).resolve()
    if path.parent != PROCESSED_VIDEO_DIR or not path.is_file():
        raise HTTPException(404, 'Media not found')
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

@app.post('/api/v1/inference/upload', response_model=InferenceVideoResponse, status_code=200, dependencies=[Depends(rate_limit)])
async def upload_video(
    request: Request,
    camera_id: str,
    max_frames: int = Query(default=300, ge=1, le=3600),
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
        with tempfile.NamedTemporaryFile(prefix='yv-video-', suffix=suffix, delete=False) as handle:
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
