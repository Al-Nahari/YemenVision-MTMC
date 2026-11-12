"""Adapters for common tracking and vehicle-ReID source layouts.

These parsers are deliberately conservative: they normalize only fields that are
present and preserve the original file as provenance. A release-specific adapter
must still be tested against its pinned manifest before production use.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from .base import DatasetAdapter
from .generic_jsonl import GenericJsonlAdapter
from ..schema import AnnotationStatus, BoundingBox, UnifiedRecord


class MotChallengeAdapter(DatasetAdapter):
    """Read MOT-style CSV or whitespace tracking annotations."""

    annotation_filename = "gt/gt.txt"
    dataset_name = "mot"

    def _jsonl_fallback(self) -> GenericJsonlAdapter | None:
        path = self.source_root / "annotations.jsonl"
        return GenericJsonlAdapter(self.source_root, release=self.release, filename=path.name) if path.is_file() else None

    def iter_records(self) -> Iterator[UnifiedRecord]:
        """Yield one record per track observation from a MOT text file."""
        fallback = self._jsonl_fallback()
        if fallback:
            yield from fallback.iter_records()
            return
        path = self.source_root / self.annotation_filename
        if not path.is_file():
            raise FileNotFoundError(f"Expected {path} or annotations.jsonl")
        camera_id = self.source_root.name
        video_id = self.source_root.name
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = [part.strip() for part in line.replace(" ", ",").split(",") if part.strip()]
            if len(parts) < 6:
                raise ValueError(f"Expected at least 6 MOT fields at {path}:{line_number}")
            try:
                frame_index = int(float(parts[0]))
                source_track_id = parts[1]
                x_min, y_min, width, height = (float(value) for value in parts[2:6])
            except ValueError as exc:
                raise ValueError(f"Invalid MOT annotation at {path}:{line_number}") from exc
            attributes: dict[str, Any] = {}
            if len(parts) >= 8:
                attributes["source_confidence"] = parts[6]
                attributes["source_class"] = parts[7]
            if len(parts) >= 9:
                attributes["source_visibility"] = parts[8]
            yield UnifiedRecord(
                image_id=f"{camera_id}:{frame_index}",
                video_id=video_id,
                camera_id=camera_id,
                frame_index=frame_index,
                vehicle_id=source_track_id,
                track_id=source_track_id,
                bbox=BoundingBox(x_min, y_min, x_min + width, y_min + height),
                vehicle_attributes=attributes,
                annotation_status={
                    "vehicle_id": AnnotationStatus.ANNOTATED,
                    "track_id": AnnotationStatus.ANNOTATED,
                    "bbox": AnnotationStatus.ANNOTATED,
                    "vehicle_type": AnnotationStatus.ANNOTATED if len(parts) >= 8 else AnnotationStatus.NOT_ANNOTATED,
                },
                **self.record_metadata(path),
            )


class UADetracXmlAdapter(DatasetAdapter):
    """Read UA-DETRAC-style XML vehicle trajectories conservatively."""

    dataset_name = "UA-DETRAC"
    annotation_filename = "annotations.xml"

    def iter_records(self) -> Iterator[UnifiedRecord]:
        """Yield records from `frame` and `target` XML elements."""
        path = self.source_root / self.annotation_filename
        if not path.is_file():
            raise FileNotFoundError(path)
        root = ET.parse(path).getroot()
        video_id = self.source_root.name
        for frame in root.iter("frame"):
            frame_index_raw = frame.attrib.get("num") or frame.attrib.get("frameID")
            if frame_index_raw is None:
                continue
            frame_index = int(frame_index_raw)
            for target in frame.iter("target"):
                target_id = target.attrib.get("id")
                vehicle = target.find("vehicle")
                box = target.find("box")
                if box is None:
                    continue
                x_min = float(box.attrib.get("left", 0))
                y_min = float(box.attrib.get("top", 0))
                width = float(box.attrib.get("width", 0))
                height = float(box.attrib.get("height", 0))
                vehicle_type = vehicle.attrib.get("type") if vehicle is not None else None
                yield UnifiedRecord(
                    image_id=f"{video_id}:{frame_index}",
                    video_id=video_id,
                    camera_id=video_id,
                    frame_index=frame_index,
                    vehicle_id=target_id,
                    track_id=target_id,
                    bbox=BoundingBox(x_min, y_min, x_min + width, y_min + height),
                    vehicle_type=vehicle_type,
                    annotation_status={
                        "vehicle_id": AnnotationStatus.ANNOTATED if target_id else AnnotationStatus.NOT_ANNOTATED,
                        "vehicle_type": AnnotationStatus.ANNOTATED if vehicle_type else AnnotationStatus.NOT_ANNOTATED,
                        "bbox": AnnotationStatus.ANNOTATED,
                    },
                    **self.record_metadata(path),
                )


class ReIdListAdapter(DatasetAdapter):
    """Read a conservative `relative_image_path identity [camera]` list."""

    dataset_name = "reid"
    list_filename = "list.txt"

    def iter_records(self) -> Iterator[UnifiedRecord]:
        """Yield image-level identity records without inventing video metadata."""
        path = self.source_root / self.list_filename
        if not path.is_file():
            raise FileNotFoundError(path)
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                raise ValueError(f"Expected image path and identity at {path}:{line_number}")
            relative_path, vehicle_id = parts[0], parts[1]
            camera_id = parts[2] if len(parts) >= 3 else None
            yield UnifiedRecord(
                image_id=relative_path,
                vehicle_id=vehicle_id,
                camera_id=camera_id,
                dataset_source=self.dataset_name,
                annotation_status={
                    "vehicle_id": AnnotationStatus.ANNOTATED,
                    "camera_id": AnnotationStatus.ANNOTATED if camera_id else AnnotationStatus.NOT_ANNOTATED,
                },
                **self.record_metadata(path),
            )
