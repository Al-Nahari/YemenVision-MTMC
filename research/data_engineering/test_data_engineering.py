"""Unit tests for the Phase 02 data foundation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from .acquisition import DownloadSpec
from .adapters import create_adapter
from .quality import validate_records
from .schema import AnnotationStatus, BoundingBox, UnifiedRecord
from .splits import SplitConfig, assign_splits, leakage_report


class SchemaTests(unittest.TestCase):
    """Verify explicit missingness and bbox validation."""

    def test_missing_fields_are_not_annotated(self) -> None:
        record = UnifiedRecord(image_id="a.jpg", dataset_source="fixture")
        self.assertEqual(record.annotation_status["vehicle_id"], AnnotationStatus.NOT_ANNOTATED)
        self.assertEqual(record.validate(), [])

    def test_invalid_bbox_is_reported(self) -> None:
        record = UnifiedRecord(
            image_id="a.jpg",
            dataset_source="fixture",
            bbox=BoundingBox(4, 4, 2, 3),
        )
        self.assertIn("bbox:max_coordinates_must_exceed_min_coordinates", record.validate())


class AdapterAndQualityTests(unittest.TestCase):
    """Verify source provenance and audit summaries."""

    def test_jsonl_adapter_and_duplicate_detection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = [
                {"image_id": "a.jpg", "camera_id": "c1", "vehicle_id": "v1"},
                {"image_id": "a.jpg", "camera_id": "c1", "vehicle_id": "v1"},
            ]
            (root / "annotations.jsonl").write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
            adapter = create_adapter("cityflow", root, "fixture-1")
            records = list(adapter.iter_records())
            report = validate_records(records)
            self.assertEqual(records[0].dataset_source, "CityFlow")
            self.assertIn("a.jpg", report["duplicate_image_ids"])


class SplitTests(unittest.TestCase):
    """Verify group-aware split behavior."""

    def test_reid_does_not_split_identity(self) -> None:
        records = [
            UnifiedRecord(image_id=f"{vehicle}-{index}", dataset_source="fixture", vehicle_id=vehicle)
            for vehicle in ("v1", "v2", "v3", "v4", "v5", "v6")
            for index in range(2)
        ]
        assign_splits(records, SplitConfig(task="reid", seed=3))
        report = leakage_report(records)
        self.assertEqual(report["vehicle_ids_crossing_splits"], [])


class AcquisitionTests(unittest.TestCase):
    """Verify that downloads are gated before network access."""

    def test_unverified_download_is_rejected(self) -> None:
        spec = DownloadSpec(
            dataset="fixture",
            release="1",
            url="https://example.invalid/file.zip",
            destination=Path("file.zip"),
            sha256="0" * 64,
            license_status="verify-before-use",
        )
        with self.assertRaises(PermissionError):
            spec.validate()


if __name__ == "__main__":
    unittest.main()
