from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Protocol

import numpy as np

from yemenvision.io import write_jsonl, write_run_manifest
from yemenvision.tracking import TrackletBuilder

LOGGER = logging.getLogger(__name__)


class CaptureProtocol(Protocol):
    fps: float
    frame_count: int | None
    width: int | None
    height: int | None

    def __iter__(self) -> Iterable[tuple[int, Any]]: ...
    def close(self) -> None: ...


class OpenCVCapture:
    def __init__(self, path: Path, vid_stride: int = 1) -> None:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("Video processing requires opencv-python; install yemenvision-mtmc[detection]") from exc
        self._capture = cv2.VideoCapture(str(path))
        if not self._capture.isOpened():
            raise RuntimeError(f"Could not open video: {path}")
        self._stride = max(1, vid_stride)
        self.fps = float(self._capture.get(cv2.CAP_PROP_FPS) or 0.0)
        if self.fps <= 0:
            raise RuntimeError(f"Video has no usable FPS metadata: {path}")
        self.frame_count = int(self._capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0) or None
        self.width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0) or None
        self.height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0) or None

    def __iter__(self) -> Iterable[tuple[int, Any]]:
        frame_index = 0
        while True:
            ok, frame = self._capture.read()
            if not ok:
                break
            if frame_index % self._stride == 0:
                yield frame_index, frame
            frame_index += 1

    def close(self) -> None:
        self._capture.release()


@dataclass(frozen=True)
class PipelineMetadata:
    camera_id: str
    fps: float
    start_time_utc: str | None = None
    vid_stride: int = 1


class OfflinePipeline:
    """Streaming detector -> camera-local tracker -> tracklets -> optional ReID."""

    def __init__(self, detector: Any, tracker: Any, encoder: Any | None = None,
                 capture_factory: Callable[[Path, int], CaptureProtocol] | None = None,
                 model_metadata: dict[str, Any] | None = None) -> None:
        self.detector, self.tracker, self.encoder = detector, tracker, encoder
        self.capture_factory = capture_factory or (lambda path, stride: OpenCVCapture(path, stride))
        self.model_metadata = model_metadata or {}

    @staticmethod
    def _embedding(crops: list[np.ndarray], encoder: Any | None) -> np.ndarray | None:
        if encoder is None or not crops:
            return None
        vectors = np.asarray(encoder.encode(crops), dtype=np.float32)
        if vectors.ndim != 2 or vectors.shape[0] == 0:
            raise ValueError("ReID encoder must return a non-empty 2D embedding array")
        mean = vectors.mean(axis=0)
        norm = float(np.linalg.norm(mean))
        if norm == 0:
            raise ValueError("mean tracklet embedding has zero norm")
        return mean / norm

    @staticmethod
    def _record_dict(record: Any, embedding: np.ndarray | None) -> dict[str, Any]:
        return {
            "camera_id": record.camera_id, "track_id": record.track_id,
            "class_name": record.class_name, "t_start": record.t_start, "t_end": record.t_end,
            "frames": record.frames, "boxes": [list(box) for box in record.boxes],
            "embedding_index": None if embedding is None else 0,
        }

    def run(self, video_path: str | Path, *, camera_id: str, output_dir: str | Path,
            metadata: PipelineMetadata | None = None, run_id: str | None = None,
            vid_stride: int = 1, max_frames: int | None = None,
            config: dict[str, Any] | None = None) -> dict[str, Any]:
        path = Path(video_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Input video does not exist: {path}")
        if vid_stride < 1:
            raise ValueError("vid_stride must be >= 1")
        capture: CaptureProtocol | None = None
        started = time.perf_counter()
        timings = {"detect_seconds": 0.0, "track_seconds": 0.0, "reid_seconds": 0.0}
        records: list[Any] = []
        track_rows: list[dict[str, Any]] = []
        embeddings: list[np.ndarray] = []
        processed = 0
        actual_metadata = metadata
        try:
            capture = self.capture_factory(path, vid_stride)
            actual_metadata = metadata or PipelineMetadata(camera_id, capture.fps, vid_stride=vid_stride)
            if abs(actual_metadata.fps - capture.fps) > 1e-6:
                raise ValueError("metadata FPS does not match video FPS")
            builder = TrackletBuilder(camera_id, capture.fps)
            processed = 0
            for frame_index, frame in capture:
                if max_frames is not None and processed >= max_frames:
                    break
                detect_start = time.perf_counter()
                detections = self.detector.detect(frame)
                timings["detect_seconds"] += time.perf_counter() - detect_start
                track_start = time.perf_counter()
                observations = self.tracker.update(frame_index, detections)
                timings["track_seconds"] += time.perf_counter() - track_start
                active_ids = set()
                for observation in observations:
                    active_ids.add(observation.track_id)
                    detection = observation.detection
                    builder.add(observation.track_id, frame_index, detection.xyxy, detection.class_name,
                                detection.confidence, frame)
                    track_rows.append({"camera_id": camera_id, "track_id": observation.track_id,
                                       "frame_index": frame_index, "timestamp": frame_index / capture.fps,
                                       "class_id": detection.class_id, "class_name": detection.class_name,
                                       "confidence": detection.confidence, "box": list(detection.xyxy),
                                       "state": observation.state})
                processed += 1
            self.tracker.finish()
            records = builder.finish()
            reid_start = time.perf_counter()
            for record in records:
                embedding = self._embedding(record.best_crops, self.encoder)
                if embedding is not None:
                    embeddings.append(embedding)
                record.embedding = None if embedding is None else embedding.tolist()
            timings["reid_seconds"] += time.perf_counter() - reid_start
        finally:
            if capture is not None:
                capture.close()
        elapsed = time.perf_counter() - started
        if run_id is None:
            identity = f"{path}:{camera_id}:{path.stat().st_size}:{path.stat().st_mtime_ns}:{vid_stride}"
            run_id = hashlib.sha256(identity.encode()).hexdigest()[:16]
        run_root = Path(output_dir) / run_id
        run_root.mkdir(parents=True, exist_ok=True)
        tracklet_rows = []
        embedding_index = []
        for index, record in enumerate(records):
            row = self._record_dict(record, None if record.embedding is None else np.asarray(record.embedding))
            row["embedding_index"] = index if record.embedding is not None else None
            tracklet_rows.append(row)
            if record.embedding is not None:
                embedding_index.append({"index": index, "camera_id": record.camera_id, "track_id": record.track_id})
        write_jsonl(run_root / "tracks.jsonl", track_rows)
        write_jsonl(run_root / "tracklets.jsonl", tracklet_rows)
        np.save(run_root / "embeddings.npy", np.stack(embeddings) if embeddings else np.empty((0, 0), dtype=np.float32))
        write_jsonl(run_root / "embeddings_index.jsonl", embedding_index)
        manifest = write_run_manifest(run_root / "run_manifest.json", models=self.model_metadata,
                                      config=config or {}, status="COMPLETED")
        manifest.update({"input": str(path), "camera_id": camera_id, "fps": capture.fps if capture else None,
                         "frames_processed": len({row['frame_index'] for row in track_rows}),
                         "tracklets": len(records), "timings": timings, "elapsed_seconds": elapsed,
                         "start_time_utc": actual_metadata.start_time_utc if 'actual_metadata' in locals() else None,
                         "synthetic_test": False})
        (run_root / "run_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        return {"status": "COMPLETED", "run_id": run_id, "output_dir": str(run_root),
                "frames_processed": manifest["frames_processed"], "tracklets_count": len(records),
                "timings": timings, "fps": manifest["frames_processed"] / elapsed if elapsed else 0.0}
