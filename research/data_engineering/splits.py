"""Task-specific, deterministic split strategies that reduce leakage."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from .schema import SplitName, UnifiedRecord


SplitTask = Literal["detection", "mot", "reid", "mtmc", "forecasting"]


@dataclass(frozen=True, slots=True)
class SplitConfig:
    """Configuration for deterministic group-aware splitting."""

    task: SplitTask
    seed: int = 17
    train_fraction: float = 0.7
    validation_fraction: float = 0.15

    def __post_init__(self) -> None:
        if not 0 < self.train_fraction < 1:
            raise ValueError("train_fraction must be between 0 and 1")
        if not 0 <= self.validation_fraction < 1:
            raise ValueError("validation_fraction must be between 0 and 1")
        if self.train_fraction + self.validation_fraction >= 1:
            raise ValueError("train and validation fractions must leave test samples")


def _stable_bucket(value: str, seed: int) -> float:
    digest = hashlib.sha256(f"{seed}:{value}".encode("utf-8")).hexdigest()
    return int(digest[:16], 16) / 16**16


def _group_key(record: UnifiedRecord, task: SplitTask) -> str:
    """Choose a leakage-control group for the requested task."""
    if task == "reid":
        return record.vehicle_id or f"image:{record.image_id}"
    if task == "mtmc":
        return record.vehicle_id or record.video_id or record.image_id
    if task in {"mot", "forecasting"}:
        return record.video_id or f"camera:{record.camera_id}:{record.image_id}"
    return record.image_id


def assign_splits(records: Iterable[UnifiedRecord], config: SplitConfig) -> list[UnifiedRecord]:
    """Return copied records with deterministic task-specific split labels."""
    materialized = list(records)
    groups: defaultdict[str, list[UnifiedRecord]] = defaultdict(list)
    for record in materialized:
        groups[_group_key(record, config.task)].append(record)

    assignments: dict[str, SplitName] = {}
    for group in groups:
        bucket = _stable_bucket(group, config.seed)
        if bucket < config.train_fraction:
            split = SplitName.TRAIN
        elif bucket < config.train_fraction + config.validation_fraction:
            split = SplitName.VALIDATION
        else:
            split = SplitName.TEST
        assignments[group] = split

    result: list[UnifiedRecord] = []
    for record in materialized:
        record.split = assignments[_group_key(record, config.task)]
        result.append(record)
    return result


def leakage_report(records: Iterable[UnifiedRecord]) -> dict[str, list[str]]:
    """Report vehicle/video groups appearing in more than one split."""
    vehicle_splits: defaultdict[str, set[str]] = defaultdict(set)
    video_splits: defaultdict[str, set[str]] = defaultdict(set)
    for record in records:
        if record.vehicle_id:
            vehicle_splits[record.vehicle_id].add(record.split.value)
        if record.video_id:
            video_splits[record.video_id].add(record.split.value)
    return {
        "vehicle_ids_crossing_splits": sorted(key for key, values in vehicle_splits.items() if len(values) > 1),
        "video_ids_crossing_splits": sorted(key for key, values in video_splits.items() if len(values) > 1),
    }
