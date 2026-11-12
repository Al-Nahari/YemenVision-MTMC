"""Unified, provenance-aware records for image, video, tracking, and ReID data.

The schema deliberately keeps source-availability separate from values. A missing
source annotation is not silently converted to a real-world unknown.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, Mapping


class AnnotationStatus(StrEnum):
    """Availability state for an annotation field."""

    ANNOTATED = "annotated"
    UNKNOWN = "unknown"
    NOT_ANNOTATED = "not_annotated"
    NOT_APPLICABLE = "not_applicable"


class SplitName(StrEnum):
    """Task-specific split names."""

    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"
    UNASSIGNED = "unassigned"


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """Pixel-space bounding box using top-left and bottom-right coordinates."""

    x_min: float
    y_min: float
    x_max: float
    y_max: float

    def validate(self, width: int | None = None, height: int | None = None) -> list[str]:
        """Return structural validation errors without mutating the box."""
        errors: list[str] = []
        if self.x_min < 0 or self.y_min < 0:
            errors.append("coordinates_must_be_non_negative")
        if self.x_max <= self.x_min or self.y_max <= self.y_min:
            errors.append("max_coordinates_must_exceed_min_coordinates")
        if width is not None and self.x_max > width:
            errors.append("x_max_exceeds_image_width")
        if height is not None and self.y_max > height:
            errors.append("y_max_exceeds_image_height")
        return errors

    def as_dict(self) -> dict[str, float]:
        """Serialize the box using the unified field names."""
        return asdict(self)


@dataclass(slots=True)
class UnifiedRecord:
    """One normalized observation with explicit provenance and annotation states."""

    image_id: str
    dataset_source: str
    video_id: str | None = None
    camera_id: str | None = None
    timestamp: str | None = None
    frame_index: int | None = None
    vehicle_id: str | None = None
    track_id: str | None = None
    bbox: BoundingBox | None = None
    vehicle_type: str | None = None
    vehicle_color: str | None = None
    vehicle_attributes: dict[str, Any] = field(default_factory=dict)
    split: SplitName = SplitName.UNASSIGNED
    annotation_status: dict[str, AnnotationStatus] = field(default_factory=dict)
    source_file: str | None = None
    source_annotation_id: str | None = None
    source_release: str | None = None
    source_sha256: str | None = None

    def __post_init__(self) -> None:
        """Apply explicit defaults for fields not provided by a source."""
        fields = (
            "video_id",
            "camera_id",
            "timestamp",
            "frame_index",
            "vehicle_id",
            "track_id",
            "bbox",
            "vehicle_type",
            "vehicle_color",
        )
        for name in fields:
            self.annotation_status.setdefault(
                name,
                AnnotationStatus.ANNOTATED if getattr(self, name) is not None else AnnotationStatus.NOT_ANNOTATED,
            )
        self.annotation_status.setdefault(
            "vehicle_attributes",
            AnnotationStatus.ANNOTATED if self.vehicle_attributes else AnnotationStatus.NOT_ANNOTATED,
        )

    def validate(self, width: int | None = None, height: int | None = None) -> list[str]:
        """Return schema and value validation errors."""
        errors: list[str] = []
        if not self.image_id.strip():
            errors.append("image_id_is_empty")
        if not self.dataset_source.strip():
            errors.append("dataset_source_is_empty")
        if self.frame_index is not None and self.frame_index < 0:
            errors.append("frame_index_must_be_non_negative")
        if self.bbox is not None:
            errors.extend(f"bbox:{error}" for error in self.bbox.validate(width, height))
        if self.vehicle_id is not None and self.annotation_status.get("vehicle_id") != AnnotationStatus.ANNOTATED:
            errors.append("vehicle_id_value_requires_annotated_status")
        return errors

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible primitives."""
        result = asdict(self)
        result["bbox"] = self.bbox.as_dict() if self.bbox else None
        result["split"] = self.split.value
        result["annotation_status"] = {key: value.value for key, value in self.annotation_status.items()}
        return result

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "UnifiedRecord":
        """Build a record from a mapping while preserving absent fields."""
        raw_bbox = data.get("bbox")
        bbox = None
        if raw_bbox is not None:
            bbox = raw_bbox if isinstance(raw_bbox, BoundingBox) else BoundingBox(**raw_bbox)
        raw_status = {
            key: value if isinstance(value, AnnotationStatus) else AnnotationStatus(value)
            for key, value in data.get("annotation_status", {}).items()
        }
        values = dict(data)
        values["bbox"] = bbox
        values["annotation_status"] = raw_status
        values["split"] = SplitName(data.get("split", SplitName.UNASSIGNED))
        return cls(**values)
