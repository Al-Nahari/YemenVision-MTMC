from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import tempfile
import os
from sqlalchemy import select, inspect, text
from urllib.parse import unquote
from sqlalchemy.orm import Session

from app.database import Base, engine, session
from app.models import AuditLog, Camera, DetectionEvent, ModelVersion, Tracklet, TrafficAggregate
from app.schemas import (
    CameraIn,
    EventIn,
    InferenceFrameRequest,
    InferenceFrameResponse,
    InferenceVideoRequest,
    InferenceVideoResponse,
    ModelIn,
    TrackletOut,
    TrafficQuery,
)
from app.security import rate_limit, require
from app.services import audit, ingest_event, run_video_inference, process_live_frame, process_uploaded_video

PROCESSED_VIDEO_DIR = Path(os.getenv('PROCESSED_VIDEO_DIR', 'processed-videos')).resolve()
PROCESSED_VIDEO_DIR.mkdir(parents=True, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    # Backward-compatible additive migration for existing SQLite development DBs.
    if engine.dialect.name == 'sqlite' and 'cameras' in inspect(engine).get_table_names():
        columns = {column['name'] for column in inspect(engine).get_columns('cameras')}
        if 'stream_url' not in columns:
            with engine.begin() as connection:
                connection.execute(text('ALTER TABLE cameras ADD COLUMN stream_url VARCHAR'))
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
    allow_origins=['http://localhost:4200', 'http://127.0.0.1:4200'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.mount('/processed-videos', StaticFiles(directory=str(PROCESSED_VIDEO_DIR)), name='processed-videos')

@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'traffic-platform', 'version': '0.2.0', 'models': ['YOLOv11m', 'OSNet ReID']}

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
    return list(db.scalars(select(Camera)).all())

@app.post('/api/v1/events', status_code=202, dependencies=[Depends(rate_limit)])
def events(body: EventIn, user=Depends(require('admin', 'operator')), db: Session = Depends(session)):
    if not db.get(Camera, body.camera_id):
        db.add(Camera(id=body.camera_id, zone="auto-zone", direction="two-way", active=True))
        db.commit()
    row, created = ingest_event(db, body, user['subject'])
    return {'id': row.id, 'status': 'accepted' if created else 'duplicate_ignored'}

@app.get('/api/v1/events', dependencies=[Depends(rate_limit)])
def list_events(
    camera_id: Optional[str] = None,
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
    camera_id: Optional[str] = None,
    video_id: Optional[str] = None,
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

@app.post('/api/v1/inference/video', response_model=InferenceVideoResponse, status_code=200, dependencies=[Depends(rate_limit)])
def infer_video(
    body: InferenceVideoRequest,
    user=Depends(require('admin', 'operator')),
    db: Session = Depends(session)
):
    if not db.get(Camera, body.camera_id):
        db.add(Camera(id=body.camera_id, zone="inference-auto", direction="two-way", active=True))
        db.commit()
    res = run_video_inference(db, body, user['subject'])
    return res

@app.post('/api/v1/inference/upload', response_model=InferenceVideoResponse, status_code=200, dependencies=[Depends(rate_limit)])
async def upload_video(
    request: Request,
    camera_id: str,
    user=Depends(require('admin', 'operator')),
    db: Session = Depends(session),
):
    """Accept the actual video bytes (not a browser-local path)."""
    content_type = request.headers.get('content-type', '')
    if not content_type.startswith('video/') and content_type != 'application/octet-stream':
        raise HTTPException(415, 'Upload a video file')
    max_bytes = 500 * 1024 * 1024
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
                    raise HTTPException(413, 'Video exceeds 500 MB limit')
                handle.write(chunk)
        if total == 0:
            raise HTTPException(400, 'Uploaded video is empty')
        if not db.get(Camera, camera_id):
            db.add(Camera(id=camera_id, zone='video-upload', direction='two-way', active=True))
            db.commit()
        body = InferenceVideoRequest(camera_id=camera_id, video_path=str(temp_path), max_frames=300)
        output_path = PROCESSED_VIDEO_DIR / f'{uuid4().hex}.mp4'
        try:
            result = process_uploaded_video(db, body, user['subject'], output_path)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(503, str(exc)) from exc
        return result.model_copy(update={'video_id': Path(original_name).stem or result.video_id})
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
def traffic(camera_id: Optional[str] = None, limit: int = 100, user=Depends(require('admin', 'operator', 'analyst')), db: Session = Depends(session)):
    q = select(TrafficAggregate).order_by(TrafficAggregate.bucket_start.desc()).limit(min(limit, 1000))
    if camera_id:
        q = q.where(TrafficAggregate.camera_id == camera_id)
    return list(db.scalars(q).all())

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
