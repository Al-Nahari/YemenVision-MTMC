import logging
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.media import media_url
from app.models import AuditLog, DetectionEvent, ProcessedVideo, Tracklet, TrafficAggregate
from app.plate_reader import engine_status, read_plate
from app.storage import put_file
from app.privacy import redact_frame
from app.schemas import (
    InferenceFrameRequest,
    InferenceFrameResponse,
    InferenceVideoRequest,
    InferenceVideoResponse,
)

LOGGER = logging.getLogger(__name__)


def json_safe(value: Any) -> Any:
    """Convert values that SQLAlchemy's JSON column cannot serialize by default."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


def audit(db: Session, actor: str, action: str, resource: str, detail: dict) -> None:
    db.add(AuditLog(
        id=str(uuid4()),
        actor=actor,
        action=action,
        resource=resource,
        detail=detail,
        occurred_at=datetime.now(timezone.utc)
    ))


def ingest_event(db: Session, event: Any, actor: str) -> tuple[DetectionEvent, bool]:
    existing = db.get(DetectionEvent, event.id)
    if existing:
        return existing, False
    row = DetectionEvent(
        id=event.id,
        camera_id=event.camera_id,
        occurred_at=event.occurred_at,
        payload={'event_type': event.event_type, **event.payload}
    )
    db.add(row)
    audit(db, actor, 'event.ingest', f'events/{event.id}', {'camera_id': event.camera_id})
    db.commit()
    return row, True


def ingest_tracklet(
    db: Session,
    camera_id: str,
    video_id: str,
    local_track_id: int,
    start_time: datetime,
    end_time: datetime,
    payload: dict,
    actor: str
) -> tuple[Tracklet, bool]:
    q = select(Tracklet).where(
        Tracklet.camera_id == camera_id,
        Tracklet.video_id == video_id,
        Tracklet.local_track_id == local_track_id
    )
    existing = db.scalars(q).first()
    if existing:
        existing.end_time = end_time
        existing.payload = payload
        db.commit()
        return existing, False

    tracklet_id = f"trk_{uuid4().hex[:16]}"
    row = Tracklet(
        id=tracklet_id,
        camera_id=camera_id,
        video_id=video_id,
        local_track_id=local_track_id,
        start_time=start_time,
        end_time=end_time,
        payload=payload
    )
    db.add(row)
    audit(db, actor, 'tracklet.ingest', f'tracklets/{tracklet_id}', {'camera_id': camera_id, 'local_track_id': local_track_id})
    db.commit()
    return row, True


class ModelManager:
    """Loads only manifest-verified models; never falls back to a different model."""

    _detector = None
    _version_name: str | None = None
    _load_lock = threading.Lock()
    _inference_lock = threading.Lock()

    @classmethod
    def get_detector(cls):
        if cls._detector is not None:
            return cls._detector
        with cls._load_lock:
            if cls._detector is not None:
                return cls._detector

            try:
                from yemenvision.registry import EXPECTED_CLASSES, ModelRegistry
            except ImportError as exc:
                raise RuntimeError(
                    'The yemenvision package is not installed; install the project package '
                    '(pip install -e .) before loading models'
                ) from exc

            registry = ModelRegistry(settings.models_dir, trusted_models_only=settings.trusted_models_only)
            requested = os.getenv('YV_DETECTOR_MODEL') or None
            try:
                record = registry.select('detector', requested)
            except (FileNotFoundError, ValueError) as exc:
                raise RuntimeError(
                    f'No verified detector is available in {settings.models_dir}: {exc}'
                ) from exc

            try:
                from ultralytics import YOLO
            except ImportError as exc:
                raise RuntimeError(
                    'Detection requires ultralytics and a working OpenCV runtime'
                ) from exc

            try:
                model = YOLO(str(record.path))
            except Exception as exc:
                raise RuntimeError(f'Could not load detector {record.path.name}: {exc}') from exc

            names = model.names
            actual = [names[i] for i in range(len(names))] if isinstance(names, dict) else list(names)
            if actual != EXPECTED_CLASSES:
                raise RuntimeError(
                    f'Detector {record.path.name} does not match the 21-class contract; '
                    'refusing to run with a different label space'
                )

            cls._detector = model
            cls._version_name = record.path.stem
            LOGGER.info('Loaded verified detector %s', record.path)
            return model

    @classmethod
    def version(cls) -> str | None:
        return cls._version_name

    @classmethod
    def inference_lock(cls) -> threading.Lock:
        # The Ultralytics tracker keeps per-model state (persist=True). Serialize
        # inference until each job owns its own tracker instance.
        return cls._inference_lock


def _annotate(frame: Any, boxes: list[list[float]], track_ids: list[int],
              confidences: list[float], class_names: list[str]) -> Any:
    import cv2

    annotated = frame.copy()
    for box, track_id, confidence, class_name in zip(boxes, track_ids, confidences, class_names):
        x1, y1, x2, y2 = (round(value) for value in box)
        color = (0, 200, 0) if track_id >= 0 else (0, 165, 255)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        label = f'{class_name} {confidence:.2f}' if track_id < 0 else f'{class_name} #{track_id} {confidence:.2f}'
        cv2.putText(annotated, label, (x1, max(12, y1 - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
    return annotated


def process_uploaded_video(
    db: Session,
    request: InferenceVideoRequest,
    actor: str,
    output_path: Path,
    progress_callback: Any | None = None,
) -> InferenceVideoResponse:
    """Run detector/tracker on an uploaded video and persist reviewable output.

    Plate numbers are read from throttled vehicle crops and stored in the event
    and tracklet logs. The video itself is only blurred when explicitly enabled
    in settings.
    """
    source = Path(request.video_path)
    if not source.is_file():
        raise ValueError('Uploaded video could not be read')
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError('Video inference requires opencv-python-headless') from exc

    detector = ModelManager.get_detector()
    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        raise ValueError('The uploaded file is not a readable video')
    fps = capture.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if width <= 0 or height <= 0:
        capture.release()
        raise ValueError('Video has invalid dimensions')
    # Cap inference resolution on weak CPUs. Frames are resized once, so both
    # detection cost and output file size drop without changing the frame count.
    if width > settings.max_infer_width:
        ratio = settings.max_infer_width / width
        width = max(160, int(width * ratio))
        height = max(90, int(height * ratio))
    display_video_id = Path(request.original_name or '').stem or source.stem
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Chrome/Edge cannot play OpenCV's default mp4v stream. VP8 in WebM is
    # supported by OpenCV's FFmpeg backend and by all modern browsers.
    writer = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*'VP80'), fps, (width, height))
    if not writer.isOpened():
        capture.release()
        raise RuntimeError('Could not create a browser-compatible processed video')

    started = time.time()
    frames = events = 0
    track_ids: dict[int, dict[str, Any]] = {}
    max_frames = request.max_frames
    try:
        while max_frames is None or frames < max_frames:
            ok, frame = capture.read()
            if not ok:
                break
            if frame.shape[1] != width or frame.shape[0] != height:
                frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
            with ModelManager.inference_lock():
                result = detector.track(
                    frame, persist=True, conf=request.conf_threshold,
                    iou=request.iou_threshold, verbose=False,
                )[0]
            frames += 1
            if progress_callback and frames % 5 == 0:
                progress_callback(frames, max_frames)
            boxes = result.boxes
            if boxes is None or len(boxes) == 0:
                writer.write(frame)
                continue

            ids = boxes.id.int().cpu().tolist() if boxes.id is not None else [-1] * len(boxes)
            coords = boxes.xyxy.cpu().tolist()
            confs = boxes.conf.cpu().tolist()
            classes = boxes.cls.int().cpu().tolist()
            names = result.names
            class_names = [str(names.get(class_id, class_id)) for class_id in classes]

            # Copy the clean frame before annotations or blur so OCR never sees
            # boxes/labels drawn over the plate region.
            ocr_source = frame.copy() if settings.plate_ocr_enabled else frame
            if settings.blur_plates:
                redact_frame(frame, coords)
            annotated = _annotate(frame, coords, ids, confs, class_names)
            writer.write(annotated)

            timestamp = datetime.now(timezone.utc)
            frame_index = frames - 1
            ocr_ready = engine_status()['available']

            # Choose a bounded set of tracks for OCR this frame. New tracks are
            # tried first, and each track gets at most two attempts, so a busy
            # scene cannot starve the last vehicles while CPU stays capped.
            ocr_targets: set[int] = set()
            if settings.plate_ocr_enabled:
                current_ids = {tid for tid in ids if tid >= 0}
                for track_id, box, class_name in zip(ids, coords, class_names):
                    if track_id < 0:
                        continue
                    track_ids.setdefault(track_id, {
                        'start': timestamp, 'end': timestamp, 'class_name': class_name,
                        'box': box, 'frames_tracked': 0, 'plate_text': None,
                        'plate_confidence': 0.0, 'plate_status': 'not_read',
                        'ocr_attempts': 0,
                    })
                pending = [
                    tid for tid in current_ids
                    if not track_ids[tid].get('plate_text')
                    and track_ids[tid].get('ocr_attempts', 0) < 2
                ]
                pending.sort(key=lambda tid: (
                    track_ids[tid]['ocr_attempts'], -track_ids[tid]['frames_tracked'],
                ))
                ocr_targets = set(pending[:settings.plate_ocr_max_per_frame])

            for track_id, box, confidence, class_id, class_name in zip(ids, coords, confs, classes, class_names):
                events += 1
                info = track_ids.setdefault(track_id, {
                    'start': timestamp, 'end': timestamp, 'class_name': class_name,
                    'box': box, 'frames_tracked': 0, 'plate_text': None,
                    'plate_confidence': 0.0, 'plate_status': 'not_read',
                    'ocr_attempts': 0,
                })
                info['end'] = timestamp
                info['box'] = box
                info['frames_tracked'] += 1
                plate = None
                if track_id in ocr_targets:
                    info['ocr_attempts'] += 1
                    plate = read_plate(ocr_source, box, settings.plate_ocr_min_confidence)
                    if not ocr_ready:
                        ocr_ready = engine_status()['available']
                    if plate and (not info['plate_text'] or plate['confidence'] > info['plate_confidence']):
                        info['plate_text'] = plate['text']
                        info['plate_confidence'] = plate['confidence']
                        info['plate_status'] = 'read'
                    elif not plate and info['plate_status'] == 'not_read':
                        info['plate_status'] = 'no_plate' if ocr_ready else 'ocr_unavailable'
                db.add(DetectionEvent(
                    id=f'evt_{uuid4().hex[:16]}', camera_id=request.camera_id,
                    occurred_at=timestamp, plate_text=info.get('plate_text'),
                    payload={
                        'event_type': 'vehicle_detection', 'video_id': display_video_id,
                        'frame_index': frame_index, 'track_id': track_id,
                        'class_id': class_id, 'class_name': class_name,
                        'confidence': float(confidence), 'box': box,
                        'plate_text': info.get('plate_text'),
                        'plate_confidence': info.get('plate_confidence', 0.0),
                        'plate_status': info.get('plate_status', 'not_read'),
                    },
                ))
    finally:
        capture.release()
        writer.release()

    if frames == 0:
        output_path.unlink(missing_ok=True)
        raise ValueError('No frames could be decoded from the uploaded video')

    for track_id, info in track_ids.items():
        if track_id < 0:
            continue
        db.add(Tracklet(
            id=f'trk_{uuid4().hex[:16]}', camera_id=request.camera_id, video_id=display_video_id,
            local_track_id=track_id, start_time=info['start'], end_time=info['end'],
            payload=json_safe({
                **info, 'model_version': ModelManager.version(), 'reid_matched': False,
                'privacy': settings.blur_mode if settings.blur_plates else 'unblurred',
            }),
        ))
    db.add(TrafficAggregate(
        id=f'agg_{uuid4().hex[:12]}', camera_id=request.camera_id,
        bucket_start=datetime.now(timezone.utc), granularity='1min',
        payload={'total_vehicles': len([key for key in track_ids if key >= 0]), 'video_id': display_video_id},
    ))
    plate_count = len([info for info in track_ids.values() if info.get('plate_text')])
    # Local disk remains available for immediate playback; S3/MinIO provides
    # durable retention when configured without changing the response contract.
    put_file(output_path, f'processed/{output_path.name}')
    db.add(ProcessedVideo(
        id=f'vid_{uuid4().hex[:16]}', file_name=output_path.name,
        original_name=request.original_name or display_video_id, video_id=display_video_id,
        camera_id=request.camera_id, created_at=datetime.now(timezone.utc),
        frames_processed=frames, duration_seconds=round(time.time() - started, 3),
        file_size=output_path.stat().st_size if output_path.exists() else 0,
        model_version=ModelManager.version(), plate_count=plate_count, source='upload',
    ))
    audit(db, actor, 'inference.video', f'videos/{display_video_id}', {
        'frames': frames, 'tracklets': len(track_ids), 'events': events,
        'plates': plate_count,
        'privacy_mode': settings.blur_mode if settings.blur_plates else 'unblurred',
    })
    db.commit()
    return InferenceVideoResponse(
        status='completed', camera_id=request.camera_id, video_id=display_video_id,
        frames_processed=frames, tracklets_count=len([key for key in track_ids if key >= 0]),
        events_count=events, duration_seconds=round(time.time() - started, 3),
        model_version=ModelManager.version() or 'unknown',
        video_url=media_url(output_path.name),
    )


def process_live_frame(db: Session, req: InferenceFrameRequest, actor: str) -> InferenceFrameResponse:
    events_generated = 0
    now = req.timestamp or datetime.now(timezone.utc)
    for det in req.detections:
        evt_id = f"evt_{uuid4().hex[:16]}"
        db.add(DetectionEvent(
            id=evt_id,
            camera_id=req.camera_id,
            occurred_at=now,
            payload={
                "event_type": "live_detection",
                "frame_index": req.frame_index,
                "class_name": det.class_name,
                "confidence": det.confidence,
                "box": det.box
            }
        ))
        events_generated += 1

    audit(db, actor, 'inference.frame', f'cameras/{req.camera_id}', {
        'frame_index': req.frame_index, 'events': events_generated,
    })
    db.commit()
    return InferenceFrameResponse(
        camera_id=req.camera_id,
        frame_index=req.frame_index,
        events_generated=events_generated,
        active_tracks=len(req.detections),
    )
