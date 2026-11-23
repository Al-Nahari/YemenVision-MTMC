from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from math import isfinite
from typing import Any

import numpy as np


@dataclass
class Tracklet:
    camera_id: str
    track_id: int
    t_start: datetime
    t_end: datetime
    embedding: list[float] | None = None
    class_name: str = "unknown"

@dataclass
class Link:
    source: tuple[str, int]
    target: tuple[str, int]
    score: float
    confidence: float
    reasons: dict[str, Any] = field(default_factory=dict)

class CrossCameraAssociator:
    def __init__(self, transitions: dict[str, dict[str, dict[str, float]]], appearance_weight: float = 0.8, threshold: float = 0.5) -> None:
        self.transitions = transitions
        self.appearance_weight = appearance_weight
        self.threshold = threshold

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        left = np.asarray(a, dtype=np.float32)
        right = np.asarray(b, dtype=np.float32)
        if left.ndim != 1 or right.ndim != 1 or left.shape != right.shape:
            raise ValueError(f"embedding dimensions do not match: {left.shape} vs {right.shape}")
        left_norm = float(np.linalg.norm(left)); right_norm = float(np.linalg.norm(right))
        if left_norm == 0.0 or right_norm == 0.0:
            raise ValueError("zero-norm embedding cannot be associated")
        return float(np.dot(left, right) / (left_norm * right_norm))

    def candidate(self, source: Tracklet, target: Tracklet) -> Link | None:
        transition = self.transitions.get(source.camera_id, {}).get(target.camera_id)
        if transition is None or source.embedding is None or target.embedding is None:
            return None
        elapsed = (target.t_start - source.t_end).total_seconds()
        if not transition["min_seconds"] <= elapsed <= transition["max_seconds"]:
            return None
        try:
            cosine = self._cosine(source.embedding, target.embedding)
        except ValueError:
            return None
        if not isfinite(cosine):
            return None
        appearance = (cosine + 1.0) / 2.0
        time_center = (transition["min_seconds"] + transition["max_seconds"]) / 2
        half_range = max((transition["max_seconds"] - transition["min_seconds"]) / 2, 1e-9)
        temporal = max(0.0, 1.0 - abs(elapsed - time_center) / half_range)
        score = self.appearance_weight * appearance + (1 - self.appearance_weight) * temporal
        return Link((source.camera_id, source.track_id), (target.camera_id, target.track_id), score, score, {"appearance_cosine": cosine, "elapsed_seconds": elapsed, "temporal_score": temporal}) if score >= self.threshold else None

    def associate(self, sources: list[Tracklet], targets: list[Tracklet]) -> list[Link]:
        candidates = [link for source in sources for target in targets if (link := self.candidate(source, target))]
        try:
            from scipy.optimize import linear_sum_assignment
        except ImportError:
            candidates.sort(key=lambda x: x.score, reverse=True)
            chosen: list[Link] = []
            used_s: set[tuple[str, int]] = set(); used_t: set[tuple[str, int]] = set()
            for link in candidates:
                if link.source not in used_s and link.target not in used_t:
                    chosen.append(link); used_s.add(link.source); used_t.add(link.target)
            return chosen
        if not candidates:
            return []
        sources_u = sorted({x.source for x in candidates}); targets_u = sorted({x.target for x in candidates})
        costs = [[1.0] * len(targets_u) for _ in sources_u]
        by_pair = {(x.source, x.target): x for x in candidates}
        for i, source in enumerate(sources_u):
            for j, target in enumerate(targets_u):
                if (item := by_pair.get((source, target))): costs[i][j] = 1 - item.score
        rows, cols = linear_sum_assignment(costs)
        return [by_pair[(sources_u[r], targets_u[c])] for r, c in zip(rows, cols) if (sources_u[r], targets_u[c]) in by_pair]
