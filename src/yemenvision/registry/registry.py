from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

EXPECTED_CLASSES = [
    "ambulance", "army vehicle", "auto rickshaw", "bicycle", "bus", "car",
    "garbagevan", "human hauler", "minibus", "minivan", "motorbike", "pickup",
    "policecar", "rickshaw", "scooter", "suv", "taxi", "three wheelers -CNG-",
    "truck", "van", "wheelbarrow",
]

@dataclass(frozen=True)
class ModelIssue:
    level: str
    message: str

@dataclass
class ModelRecord:
    path: Path
    kind: str
    sha256: str | None = None
    size_bytes: int = 0
    issues: list[ModelIssue] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def valid(self) -> bool:
        return not any(i.level == "ERROR" for i in self.issues)

class ModelRegistry:
    """Read-only model discovery and validation; loading is deliberately lazy."""
    def __init__(self, models_dir: str | Path | None = None, manifest_name: str = "manifest.json") -> None:
        self.models_dir = Path(models_dir or os.getenv("YV_MODELS_DIR", "models")).expanduser().resolve()
        self.manifest_path = self.models_dir / manifest_name
        self._manifest = self._read_manifest()

    def _read_manifest(self) -> dict[str, Any]:
        if not self.manifest_path.exists():
            return {}
        try:
            data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _kind(path: Path) -> str:
        name = path.name.lower()
        if name.startswith("reid_attr_"):
            return "reid_attribute"
        if "reid" in name:
            return "reid"
        return "detector"

    @staticmethod
    def sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    def discover(self) -> list[ModelRecord]:
        if not self.models_dir.exists():
            return []
        records = []
        for path in sorted(self.models_dir.glob("*.pt")):
            record = ModelRecord(path=path, kind=self._kind(path), size_bytes=path.stat().st_size)
            record.sha256 = self.sha256(path)
            if path.name.lower().endswith("_last.pt"):
                record.issues.append(ModelIssue("ERROR", "checkpoint *_last.pt is not valid for inference"))
            if record.kind == "reid_attribute":
                record.issues.append(ModelIssue("ERROR", "synthetic attribute checkpoint is not production ReID"))
            expected = self._manifest.get("models", {}).get(path.name)
            if expected and expected != record.sha256:
                record.issues.append(ModelIssue("ERROR", "SHA-256 does not match manifest.json"))
            if not expected and self._manifest.get("models"):
                record.issues.append(ModelIssue("WARNING", "model is absent from manifest.json"))
            inspected = self.validate_checkpoint(path)
            record.metadata.update(inspected.metadata)
            record.issues.extend(inspected.issues)
            records.append(record)
        return records

    def select(self, kind: str, name: str | None = None) -> ModelRecord:
        records = [r for r in self.discover() if r.kind == kind]
        if name:
            records = [r for r in records if r.path.name == name]
        if kind == "detector":
            records.sort(key=lambda r: (r.path.name not in {"best.pt", "detection_yolo11s_best.pt"}, r.path.name))
        else:
            records.sort(key=lambda r: (r.path.name != "reid_bot_best.pt", r.path.name))
        if not records:
            raise FileNotFoundError(f"No {kind} model found in {self.models_dir}")
        record = records[0]
        if not record.valid:
            raise ValueError(f"Invalid model {record.path.name}: " + "; ".join(i.message for i in record.issues))
        return record

    def validate_checkpoint(self, path: str | Path) -> ModelRecord:
        """Validate a checkpoint structure without importing torch until needed."""
        target = Path(path)
        record = ModelRecord(target, self._kind(target), target.stat().st_size if target.exists() else 0)
        if not target.exists():
            record.issues.append(ModelIssue("ERROR", "file does not exist"))
            return record
        record.sha256 = self.sha256(target)
        try:
            import torch
            checkpoint = torch.load(target, map_location="cpu", weights_only=False)
        except ImportError:
            record.issues.append(ModelIssue("ERROR", "torch is not installed; checkpoint internals could not be validated"))
            return record
        except Exception as exc:
            record.issues.append(ModelIssue("ERROR", f"checkpoint could not be read: {exc}"))
            return record
        if record.kind == "detector":
            names = getattr(checkpoint, "names", None)
            if names is None and isinstance(checkpoint, dict):
                names = checkpoint.get("names")
            if names is not None:
                actual = [names[i] for i in range(len(names))] if isinstance(names, dict) else list(names)
                record.metadata["classes"] = actual
                if actual != EXPECTED_CLASSES:
                    record.issues.append(ModelIssue("ERROR", "detector class names do not match the 21-class contract"))
        else:
            cfg = checkpoint.get("cfg") if isinstance(checkpoint, dict) else None
            state = checkpoint.get("state_dict") if isinstance(checkpoint, dict) else None
            if not isinstance(cfg, dict) or cfg.get("backbone") != "resnet50" or tuple(cfg.get("size", ())) != (224, 224):
                record.issues.append(ModelIssue("ERROR", "ReID cfg must declare resnet50 and size (224, 224)"))
            keys = set(state or {})
            if not any(k.startswith("backbone.") for k in keys) or not any(k.startswith("bn.") or k.startswith("bnneck.") for k in keys):
                record.issues.append(ModelIssue("ERROR", "ReID checkpoint must contain backbone and BNNeck weights"))
        return record
