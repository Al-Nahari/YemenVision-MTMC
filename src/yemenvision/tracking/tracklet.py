from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

@dataclass
class TrackletRecord:
    camera_id: str
    track_id: int
    class_name: str
    t_start: float
    t_end: float
    frames: list[int] = field(default_factory=list)
    boxes: list[tuple[float, float, float, float]] = field(default_factory=list)
    best_crops: list[Any] = field(default_factory=list)

class TrackletBuilder:
    def __init__(self, camera_id: str) -> None:
        self.camera_id = camera_id
        self._records: dict[int, TrackletRecord] = {}

    def add(self, track_id: int, frame_index: int, timestamp: float, box: tuple[float, float, float, float], class_name: str) -> None:
        record = self._records.get(track_id)
        if record is None:
            record = TrackletRecord(self.camera_id, track_id, class_name, timestamp, timestamp)
            self._records[track_id] = record
        record.t_end = timestamp
        record.frames.append(frame_index); record.boxes.append(box)
        record.class_name = class_name

    def finish(self) -> list[TrackletRecord]:
        return list(self._records.values())
