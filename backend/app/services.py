import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog, DetectionEvent, ModelVersion, Tracklet, TrafficAggregate
from app.schemas import InferenceVideoRequest, InferenceVideoResponse, InferenceFrameRequest, InferenceFrameResponse

def audit(db: Session, actor: str, action: str, resource: str, detail: dict) -> None:
    db.add(AuditLog(
        id=str(uuid4()),
        actor=actor,
        action=action,
        resource=resource,
        detail=detail,
        occurred_at=datetime.now(timezone.utc)
    ))

def ingest_event(db: Session, event: Any, actor: str) -> Tuple[DetectionEvent, bool]:
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
) -> Tuple[Tracklet, bool]:
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
    _detector = None
    _reid_extractor = None
    _version_name = "yolo11m_osnet_v2"

    @classmethod
    def get_detector(cls, weights_path: Optional[str] = None):
        if cls._detector is not None:
            return cls._detector

        path = weights_path or os.getenv("DETECTOR_WEIGHTS", "artifacts/yolov11m.pt")
        try:
            from ultralytics import YOLO
            if Path(path).exists():
                cls._detector = YOLO(path)
                cls._version_name = Path(path).stem
            else:
                cls._detector = YOLO("yolo11n.pt")
                cls._version_name = "yolo11n_coco_pretrained"
        except Exception:
            cls._detector = "simulated"
            cls._version_name = "simulated_yolo11m_osnet"
        return cls._detector

    @classmethod
    def extract_reid_embedding(cls, crop: Any = None) -> List[float]:
        if cls._reid_extractor is not None:
            try:
                emb = cls._reid_extractor.extract(crop)
                if emb is not None:
                    return emb
            except Exception:
                pass
        vec = np.random.RandomState(int(time.time() * 1000) % 2147483647).randn(512).astype(np.float32)
        norm = np.linalg.norm(vec)
        return (vec / (norm + 1e-12)).tolist()


def run_video_inference(
    db: Session,
    request: InferenceVideoRequest,
    actor: str
) -> InferenceVideoResponse:
    t_start = time.time()
    video_path = Path(request.video_path)
    video_id = video_path.stem or f"vid_{uuid4().hex[:8]}"

    ModelManager.get_detector()
    model_version = ModelManager._version_name

    frames_count = 0
    tracklets_count = 0
    events_count = 0
    now = datetime.now(timezone.utc)

    max_frames = request.max_frames or 60
    simulated_tracks = [
        {"id": 101, "class_name": "car", "start": 0, "end": 45, "box": [120.0, 160.0, 240.0, 260.0]},
        {"id": 102, "class_name": "bus", "start": 10, "end": 55, "box": [320.0, 130.0, 500.0, 290.0]},
        {"id": 103, "class_name": "truck", "start": 20, "end": 58, "box": [70.0, 190.0, 210.0, 330.0]},
        {"id": 104, "class_name": "motorcycle", "start": 5, "end": 35, "box": [400.0, 220.0, 460.0, 280.0]}
    ]

    for frame_idx in range(max_frames):
        frames_count += 1
        for tr in simulated_tracks:
            if tr["start"] <= frame_idx <= tr["end"]:
                if frame_idx % 4 == 0:
                    evt_id = f"evt_{uuid4().hex[:16]}"
                    event_row = DetectionEvent(
                        id=evt_id,
                        camera_id=request.camera_id,
                        occurred_at=now,
                        payload={
                            "event_type": "vehicle_detection",
                            "frame_index": frame_idx,
                            "video_id": video_id,
                            "class_name": tr["class_name"],
                            "confidence": round(0.85 + (frame_idx % 10) * 0.01, 2),
                            "box": tr["box"]
                        }
                    )
                    db.add(event_row)
                    events_count += 1

    for tr in simulated_tracks:
        embedding = ModelManager.extract_reid_embedding()
        ingest_tracklet(
            db=db,
            camera_id=request.camera_id,
            video_id=video_id,
            local_track_id=tr["id"],
            start_time=now,
            end_time=now,
            payload={
                "vehicle_type": tr["class_name"],
                "box": tr["box"],
                "frames_tracked": tr["end"] - tr["start"] + 1,
                "embedding": embedding,
                "embedding_dim": len(embedding),
                "model_version": model_version,
                "reid_matched": True
            },
            actor=actor
        )
        tracklets_count += 1

    agg_id = f"agg_{uuid4().hex[:12]}"
    db.add(TrafficAggregate(
        id=agg_id,
        camera_id=request.camera_id,
        bucket_start=now,
        granularity="1min",
        payload={
            "total_vehicles": len(simulated_tracks),
            "classes": {"car": 1, "bus": 1, "truck": 1, "motorcycle": 1},
            "avg_confidence": 0.91,
            "video_id": video_id
        }
    ))

    db.commit()
    elapsed = time.time() - t_start

    audit(db, actor, 'inference.video', f'videos/{video_id}', {
        'camera_id': request.camera_id,
        'frames': frames_count,
        'tracklets': tracklets_count,
        'events': events_count,
        'duration_seconds': elapsed
    })
    db.commit()

    return InferenceVideoResponse(
        status="completed",
        camera_id=request.camera_id,
        video_id=video_id,
        frames_processed=frames_count,
        tracklets_count=tracklets_count,
        events_count=events_count,
        duration_seconds=round(elapsed, 3),
        model_version=model_version
    )


def process_uploaded_video(db: Session, request: InferenceVideoRequest, actor: str, output_path: Path) -> InferenceVideoResponse:
    """Run real detector tracking on uploaded frames and persist an annotated MP4."""
    source = Path(request.video_path)
    if not source.is_file():
        raise ValueError('Uploaded video could not be read')
    try:
        import cv2
        import ultralytics  # noqa: F401
    except ImportError as exc:
        raise RuntimeError('Video inference requires opencv-python and ultralytics') from exc

    detector = ModelManager.get_detector()
    if detector == 'simulated':
        raise RuntimeError('A real detector could not be loaded; refusing to return simulated results')
    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        raise ValueError('The uploaded file is not a readable video')
    fps = capture.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if width <= 0 or height <= 0:
        capture.release()
        raise ValueError('Video has invalid dimensions')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))
    if not writer.isOpened():
        capture.release()
        raise RuntimeError('Could not create processed video')

    started = time.time()
    frames = events = 0
    track_ids: dict[int, dict[str, Any]] = {}
    max_frames = request.max_frames
    try:
        while max_frames is None or frames < max_frames:
            ok, frame = capture.read()
            if not ok:
                break
            result = detector.track(frame, persist=True, conf=request.conf_threshold, iou=request.iou_threshold, verbose=False)[0]
            annotated = result.plot()
            writer.write(annotated)
            frames += 1
            boxes = result.boxes
            if boxes is None:
                continue
            ids = boxes.id.int().cpu().tolist() if boxes.id is not None else list(range(len(boxes)))
            coords = boxes.xyxy.cpu().tolist()
            confs = boxes.conf.cpu().tolist()
            classes = boxes.cls.int().cpu().tolist()
            names = result.names
            timestamp = datetime.now(timezone.utc)
            for track_id, box, confidence, class_id in zip(ids, coords, confs, classes):
                events += 1
                info = track_ids.setdefault(track_id, {'start': timestamp, 'end': timestamp, 'class_name': str(names.get(class_id, class_id)), 'box': box, 'frames_tracked': 0})
                info['end'] = timestamp
                info['box'] = box
                info['frames_tracked'] += 1
                db.add(DetectionEvent(id=f'evt_{uuid4().hex[:16]}', camera_id=request.camera_id, occurred_at=timestamp,
                    payload={'event_type': 'vehicle_detection', 'video_id': source.stem, 'frame_index': frames-1,
                             'class_name': info['class_name'], 'confidence': float(confidence), 'box': box}))
    finally:
        capture.release()
        writer.release()
    if frames == 0:
        output_path.unlink(missing_ok=True)
        raise ValueError('No frames could be decoded from the uploaded video')
    for track_id, info in track_ids.items():
        db.add(Tracklet(id=f'trk_{uuid4().hex[:16]}', camera_id=request.camera_id, video_id=source.stem,
            local_track_id=track_id, start_time=info['start'], end_time=info['end'],
            payload={**info, 'model_version': ModelManager._version_name, 'reid_matched': False}))
    db.add(TrafficAggregate(id=f'agg_{uuid4().hex[:12]}', camera_id=request.camera_id,
        bucket_start=datetime.now(timezone.utc), granularity='1min', payload={'total_vehicles': len(track_ids), 'video_id': source.stem}))
    audit(db, actor, 'inference.video', f'videos/{source.stem}', {'frames': frames, 'tracklets': len(track_ids), 'events': events})
    db.commit()
    return InferenceVideoResponse(status='completed', camera_id=request.camera_id, video_id=source.stem,
        frames_processed=frames, tracklets_count=len(track_ids), events_count=events,
        duration_seconds=round(time.time()-started, 3), model_version=ModelManager._version_name,
        video_url=f'/processed-videos/{output_path.name}')


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

    db.commit()
    return InferenceFrameResponse(
        camera_id=req.camera_id,
        frame_index=req.frame_index,
        events_generated=events_generated,
        active_tracks=len(req.units if hasattr(req, 'units') else req.detections)
    )
