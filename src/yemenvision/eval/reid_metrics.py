from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class ReIDMetrics:
    map: float
    rank1: float
    rank5: float
    rank10: float
    evaluated_queries: int

    def as_dict(self) -> dict[str, float | int]:
        return {"mAP": self.map, "rank1": self.rank1, "rank5": self.rank5,
                "rank10": self.rank10, "evaluated_queries": self.evaluated_queries}


def check_identity_leakage(train_ids: Iterable[str], test_ids: Iterable[str]) -> None:
    overlap = set(train_ids).intersection(test_ids)
    if overlap:
        raise ValueError(f"identity leakage detected: {len(overlap)} identities overlap")


def evaluate_reid(query_embeddings: np.ndarray, query_ids: np.ndarray, query_cameras: np.ndarray,
                  gallery_embeddings: np.ndarray, gallery_ids: np.ndarray, gallery_cameras: np.ndarray) -> ReIDMetrics:
    if len(query_embeddings) != len(query_ids) or len(query_ids) != len(query_cameras):
        raise ValueError("query arrays have inconsistent lengths")
    if len(gallery_embeddings) != len(gallery_ids) or len(gallery_ids) != len(gallery_cameras):
        raise ValueError("gallery arrays have inconsistent lengths")
    if len(query_embeddings) == 0 or len(gallery_embeddings) == 0:
        raise ValueError("query and gallery must be non-empty")
    similarities = query_embeddings @ gallery_embeddings.T
    average_precisions: list[float] = []; hits = {1: 0, 5: 0, 10: 0}
    evaluated = 0
    for index, (identity, camera) in enumerate(zip(query_ids, query_cameras)):
        valid = ~((gallery_ids == identity) & (gallery_cameras == camera))
        order = np.argsort(-similarities[index], kind="stable")[valid[np.argsort(-similarities[index], kind="stable")]]
        matches = gallery_ids[order] == identity
        if not matches.any():
            continue
        evaluated += 1
        cumulative = np.cumsum(matches)
        precision = cumulative / np.arange(1, len(matches) + 1)
        average_precisions.append(float((precision * matches).sum() / matches.sum()))
        for rank in hits:
            hits[rank] += int(matches[:rank].any())
    if not evaluated:
        raise ValueError("no query has a valid positive gallery match")
    return ReIDMetrics(float(np.mean(average_precisions)), *(hits[r] / evaluated for r in (1, 5, 10)), evaluated)
