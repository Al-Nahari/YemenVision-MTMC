"""Adapter for normalized or nearly-normalized JSONL fixtures and releases."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from .base import DatasetAdapter
from ..schema import UnifiedRecord


class GenericJsonlAdapter(DatasetAdapter):
    """Read one JSON object per line and preserve source provenance."""

    dataset_name = "generic_jsonl"

    def __init__(self, source_root: Path, release: str = "unknown", filename: str = "annotations.jsonl") -> None:
        super().__init__(source_root, release)
        self.annotation_path = source_root / filename

    def iter_records(self) -> Iterator[UnifiedRecord]:
        """Yield records from the configured JSONL file."""
        if not self.annotation_path.is_file():
            raise FileNotFoundError(self.annotation_path)
        for raw in self.read_jsonl(self.annotation_path):
            values = dict(raw)
            values.update(self.record_metadata(self.annotation_path))
            yield UnifiedRecord.from_mapping(values)
