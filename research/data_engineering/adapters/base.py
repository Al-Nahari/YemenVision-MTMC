"""Base interface for dataset-to-unified-schema adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from ..schema import UnifiedRecord


class DatasetAdapter(ABC):
    """Convert one source release into validated unified records."""

    dataset_name: str

    def __init__(self, source_root: Path, release: str = "unknown") -> None:
        self.source_root = source_root
        self.release = release

    @abstractmethod
    def iter_records(self) -> Iterator[UnifiedRecord]:
        """Yield normalized observations from the source release."""
        raise NotImplementedError

    def read_jsonl(self, path: Path) -> Iterable[dict[str, Any]]:
        """Read JSON Lines without assuming all optional fields exist."""
        import json

        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSONL at {path}:{line_number}") from exc
                if not isinstance(value, dict):
                    raise ValueError(f"Expected an object at {path}:{line_number}")
                yield value

    def record_metadata(self, source_file: Path) -> dict[str, str]:
        """Return provenance fields shared by adapter implementations."""
        return {
            "dataset_source": self.dataset_name,
            "source_file": str(source_file),
            "source_release": self.release,
        }
