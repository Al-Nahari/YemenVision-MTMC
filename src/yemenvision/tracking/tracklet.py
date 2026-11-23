from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class CropCandidate:
    image: np.ndarray
    frame_index: int
    area: float
    sharpness: float
    edge_margin: float
    confidence: float

    @property
    def quality(self) -> float:
        return self.area * (1.0 + max(0.0, self.sharpness)) * max(0.0, self.edge_margin) * self.confidence


@dataclass
class TrackletRecord:
    camera_id: str
    track_id: int
    class_name: str
    t_start: float
    t_end: float
    frames: list[int] = field(default_factory=list)
    boxes: list[tuple[float, float, float, float]] = field(default_factory=list)
    best_crops: list[np.ndarray] = field(default_factory=list)
    embedding: list[float] | None = None


class TrackletBuilder:
    """Build bounded tracklets using timestamps derived from the source FPS."""

    def __init__(self, camera_id: str, fps: float, max_crops: int = 8, max_crop_memory_mb: int = 128) -> None:
        if fps <= 0:
            raise ValueError("fps must be positive")
        self.camera_id = camera_id
        self.fps = fps
        self.max_crops = max_crops
        self.max_crop_bytes = max_crop_memory_mb * 1024 * 1024
        self._records: dict[int, TrackletRecord] = {}
        self._crops: dict[int, list[CropCandidate]] = {}
        self._crop_bytes = 0
        self._classes: dict[int, Counter[str]] = {}

    def add(self, track_id: int, frame_index: int, box: tuple[float, float, float, float],
            class_name: str, confidence: float, frame: np.ndarray | None = None) -> None:
        timestamp = frame_index / self.fps
        record = self._records.get(track_id)
        if record is None:
            record = TrackletRecord(self.camera_id, track_id, class_name, timestamp, timestamp)
            self._records[track_id] = record
            self._classes[track_id] = Counter()
        record.t_end = timestamp
        record.frames.append(frame_index)
        record.boxes.append(box)
        self._classes[track_id][class_name] += 1
        record.class_name = self._classes[track_id].most_common(1)[0][0]
        if frame is not None:
            candidate = self._candidate(frame, frame_index, box, confidence)
            if candidate is not None:
                self._add_crop(track_id, candidate)

    @staticmethod
    def _candidate(frame: np.ndarray, frame_index: int, box: tuple[float, float, float, float], confidence: float) -> CropCandidate | None:
        height, width = frame.shape[:2]
        x1, y1, x2, y2 = (round(value) for value in box)
        clipped = (max(0, x1), max(0, y1), min(width, x2), min(height, y2))
        if clipped[2] <= clipped[0] or clipped[3] <= clipped[1]:
            return None
        crop = frame[clipped[1]:clipped[3], clipped[0]:clipped[2]].copy()
        if crop.size == 0:
            return None
        gray = crop.mean(axis=2) if crop.ndim == 3 else crop
        sharpness = float(np.var(np.diff(gray.astype(np.float32), axis=0))) if gray.shape[0] > 1 else 0.0
        margin = min(clipped[0], clipped[1], width - clipped[2], height - clipped[3]) / max(width, height)
        return CropCandidate(crop, frame_index, float(crop.shape[0] * crop.shape[1]), sharpness, margin, confidence)

    def _add_crop(self, track_id: int, candidate: CropCandidate) -> None:
        current = self._crops.setdefault(track_id, [])
        self._crop_bytes += int(candidate.image.nbytes)
        current.append(candidate)
        current.sort(key=lambda item: (-item.quality, item.frame_index))
        while len(current) > self.max_crops:
            self._crop_bytes -= int(current.pop().image.nbytes)
        while self._crop_bytes > self.max_crop_bytes and current:
            self._crop_bytes -= int(current.pop().image.nbytes)

    def close(self, track_id: int) -> TrackletRecord | None:
        record = self._records.pop(track_id, None)
        if record is None:
            return None
        record.best_crops = [item.image for item in self._crops.pop(track_id, [])]
        self._classes.pop(track_id, None)
        self._crop_bytes = sum(int(item.image.nbytes) for values in self._crops.values() for item in values)
        return record

    def finish(self) -> list[TrackletRecord]:
        records = [self.close(track_id) for track_id in sorted(self._records)]
        return [record for record in records if record is not None]
