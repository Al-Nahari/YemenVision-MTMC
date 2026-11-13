from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Protocol, Iterable

@dataclass(frozen=True)
class Detection:
    xyxy: tuple[float, float, float, float]
    confidence: float
    class_id: int
    class_name: str = "vehicle"

@dataclass
class TrackEvent:
    frame_index: int
    camera_id: str
    video_id: str
    track_id: int  # local to this camera+video only
    state: str
    xyxy: list[float]
    confidence: float
    class_id: int
    class_name: str
    def to_dict(self): return asdict(self)

class Detector(Protocol):
    def detect(self, frame) -> Iterable[Detection]: ...
