"""Dataset integrity, annotation, duplication, and distribution audits."""

from __future__ import annotations

import hashlib
import json
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .schema import UnifiedRecord

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class FileCheck:
    """Integrity result for one local file."""

    path: str
    exists: bool
    size_bytes: int
    sha256: str | None
    readable: bool
    error: str | None = None


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Hash a file incrementally to avoid loading it into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_file(path: Path) -> FileCheck:
    """Check existence, size, and read access for a file."""
    if not path.is_file():
        return FileCheck(str(path), False, 0, None, False, "file_not_found")
    try:
        size = path.stat().st_size
        digest = sha256_file(path)
        return FileCheck(str(path), True, size, digest, True)
    except (OSError, PermissionError) as exc:
        return FileCheck(str(path), True, 0, None, False, str(exc))


def validate_records(records: Iterable[UnifiedRecord]) -> dict[str, Any]:
    """Validate records and summarize missing annotations and distributions."""
    errors: list[dict[str, Any]] = []
    missing: Counter[str] = Counter()
    types: Counter[str] = Counter()
    cameras: Counter[str] = Counter()
    identities: Counter[str] = Counter()
    image_keys: defaultdict[str, list[int]] = defaultdict(list)
    total = 0

    for index, record in enumerate(records):
        total += 1
        record_errors = record.validate()
        if record_errors:
            errors.append({"record_index": index, "image_id": record.image_id, "errors": record_errors})
        for field_name, status in record.annotation_status.items():
            if status.value != "annotated":
                missing[f"{field_name}:{status.value}"] += 1
        if record.vehicle_type:
            types[record.vehicle_type] += 1
        if record.camera_id:
            cameras[record.camera_id] += 1
        if record.vehicle_id:
            identities[record.vehicle_id] += 1
        image_keys[record.image_id].append(index)

    duplicates = {key: indexes for key, indexes in image_keys.items() if len(indexes) > 1}
    return {
        "record_count": total,
        "invalid_record_count": len(errors),
        "errors": errors,
        "missing_annotation_counts": dict(missing),
        "vehicle_type_counts": dict(types),
        "camera_counts": dict(cameras),
        "identity_observation_counts": dict(identities),
        "duplicate_image_ids": duplicates,
    }


def write_json_report(report: dict[str, Any], output_path: Path) -> None:
    """Write a stable, indented JSON report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
