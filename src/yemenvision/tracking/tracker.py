from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from yemenvision.detection import Detection


class SingleCameraTracker(Protocol):
    """Camera-local tracker contract. IDs are never global identities."""

    def update(self, frame_index: int, detections: Sequence[Detection]) -> list[TrackObservation]: ...
    def finish(self) -> list[TrackObservation]: ...


@dataclass(frozen=True)
class TrackObservation:
    track_id: int
    detection: Detection
    state: str = "active"


def iou(left: tuple[float, float, float, float], right: tuple[float, float, float, float]) -> float:
    x1 = max(left[0], right[0]); y1 = max(left[1], right[1])
    x2 = min(left[2], right[2]); y2 = min(left[3], right[3])
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    left_area = max(0.0, left[2] - left[0]) * max(0.0, left[3] - left[1])
    right_area = max(0.0, right[2] - right[0]) * max(0.0, right[3] - right[1])
    union = left_area + right_area - intersection
    return intersection / union if union else 0.0


@dataclass
class _ActiveTrack:
    track_id: int
    detection: Detection
    missed: int = 0


class IoUTracker:
    """Small deterministic tracker used when a dedicated ByteTrack adapter is unavailable."""

    def __init__(self, match_thresh: float = 0.8, track_buffer: int = 50, new_track_thresh: float = 0.25) -> None:
        if not 0 <= match_thresh <= 1:
            raise ValueError("match_thresh must be in [0, 1]")
        self.match_thresh = match_thresh
        self.track_buffer = track_buffer
        self.new_track_thresh = new_track_thresh
        self._tracks: dict[int, _ActiveTrack] = {}
        self._next_id = 1

    def update(self, frame_index: int, detections: Sequence[Detection]) -> list[TrackObservation]:
        del frame_index  # IDs are scoped to this tracker instance, not frame identifiers.
        candidates = [d for d in detections if d.confidence >= self.new_track_thresh]
        pairs = sorted(
            ((iou(track.detection.xyxy, detection.xyxy), track_id, index)
             for track_id, track in self._tracks.items()
             for index, detection in enumerate(candidates)
             if track.detection.class_id == detection.class_id),
            key=lambda item: (-item[0], item[1], item[2]),
        )
        used_tracks: set[int] = set(); used_detections: set[int] = set()
        for overlap, track_id, index in pairs:
            if overlap < self.match_thresh or track_id in used_tracks or index in used_detections:
                continue
            self._tracks[track_id].detection = candidates[index]
            self._tracks[track_id].missed = 0
            used_tracks.add(track_id); used_detections.add(index)
        for track_id, track in self._tracks.items():
            if track_id not in used_tracks:
                track.missed += 1
        for index, detection in enumerate(candidates):
            if index not in used_detections:
                self._tracks[self._next_id] = _ActiveTrack(self._next_id, detection)
                self._next_id += 1
        self._tracks = {track_id: track for track_id, track in self._tracks.items()
                        if track.missed <= self.track_buffer}
        return [TrackObservation(track_id, self._tracks[track_id].detection)
                for track_id in sorted(self._tracks)]

    def finish(self) -> list[TrackObservation]:
        observations = [TrackObservation(track_id, track.detection, "closed")
                        for track_id, track in sorted(self._tracks.items())]
        self._tracks.clear()
        return observations
