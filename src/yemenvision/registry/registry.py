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
        return not any(issue.level == "ERROR" for issue in self.issues)

    def as_dict(self) -> dict[str, Any]:
        return {"path": str(self.path), "kind": self.kind, "sha256": self.sha256,
                "size_bytes": self.size_bytes, "valid": self.valid,
                "issues": [{"level": i.level, "message": i.message} for i in self.issues],
                "metadata": self.metadata}

class ModelRegistry:
    """Read-only model discovery with content hashing and optional trusted loading.

    PyTorch checkpoints are executable pickle containers. Set ``trusted_models_only``
    (recommended) to require a manifest hash before any checkpoint deserialization.
    """
    def __init__(self, models_dir: str | Path | None = None, manifest_name: str = "manifest.json",
                 trusted_models_only: bool = False) -> None:
        self.models_dir = Path(models_dir or os.getenv("YV_MODELS_DIR", "models")).expanduser().resolve()
        self.manifest_path = self.models_dir / manifest_name
        self.trusted_models_only = trusted_models_only
        self._manifest = self._read_manifest()
        self._hash_cache: dict[tuple[str, int, int], str] = {}
        self._records: list[ModelRecord] | None = None

    def _read_manifest(self) -> dict[str, Any]:
        if not self.manifest_path.exists():
            return {}
        try:
            value = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _kind(path: Path) -> str:
        name = path.name.lower()
        if name.startswith("reid_attr_") or name == "vehicle_attributes.pt":
            return "reid_attribute"
        if "reid" in name:
            return "reid"
        return "detector"

    def sha256(self, path: Path) -> str:
        stat = path.stat()
        key = (str(path), stat.st_size, stat.st_mtime_ns)
        if key not in self._hash_cache:
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(block)
            self._hash_cache[key] = digest.hexdigest()
        return self._hash_cache[key]

    def _expected_hash(self, name: str) -> str | None:
        value = self._manifest.get("models", {}).get(name)
        if isinstance(value, dict):
            return value.get("sha256")
        return value if isinstance(value, str) else None

    def _base_record(self, path: Path) -> ModelRecord:
        record = ModelRecord(path=path, kind=self._kind(path), size_bytes=path.stat().st_size)
        record.sha256 = self.sha256(path)
        if path.name.lower().endswith("_last.pt"):
            record.issues.append(ModelIssue("ERROR", "checkpoint *_last.pt is not valid for inference"))
        if record.kind == "reid_attribute" and path.name == "vehicle_attributes.pt":
            # vehicle_attributes.pt is an auxiliary model, not invalid for inference generally
            pass
        elif record.kind == "reid_attribute":
            record.issues.append(ModelIssue("ERROR", "synthetic attribute checkpoint is not production ReID"))
        expected = self._expected_hash(path.name)
        if expected and expected != record.sha256:
            record.issues.append(ModelIssue("ERROR", "SHA-256 does not match manifest.json"))
        if self.trusted_models_only and expected != record.sha256:
            record.issues.append(ModelIssue("ERROR", "trusted_models_only requires a matching manifest SHA-256"))
        elif not expected and self._manifest.get("models"):
            record.issues.append(ModelIssue("WARNING", "model is absent from manifest.json"))
        return record

    def discover(self, refresh: bool = False) -> list[ModelRecord]:
        if self._records is not None and not refresh:
            return self._records
        if not self.models_dir.exists():
            self._records = []
            return self._records
        records: list[ModelRecord] = []
        for path in sorted(self.models_dir.glob("*.pt")):
            record = self._base_record(path)
            # Never deserialize known-invalid checkpoint names. For other files, inspect
            # only when explicitly trusted or when a manifest hash matches.
            if record.valid and (self.trusted_models_only or self._expected_hash(path.name) == record.sha256):
                inspected = self.validate_checkpoint(path, _hash_already_computed=True)
                record.metadata.update(inspected.metadata)
                record.issues.extend(inspected.issues)
            records.append(record)
        self._records = records
        return records

    def select(self, kind: str, name: str | None = None) -> ModelRecord:
        records = [r for r in self.discover() if r.kind == kind and (name is None or r.path.name == name)]
        if kind == "detector":
            preferred = {"detector_best.pt", "best.pt", "detection_yolo11s_best.pt"}
        else:
            preferred = {"reid_best.pt", "reid_bot_best.pt"}
        records.sort(key=lambda r: (r.path.name not in preferred, r.path.name))
        if not records:
            raise FileNotFoundError(f"No {kind} model found in {self.models_dir}")
        record = records[0]
        if not record.valid:
            raise ValueError(f"Invalid model {record.path.name}: " + "; ".join(i.message for i in record.issues))
        return record

    def validate_checkpoint(self, path: str | Path, _hash_already_computed: bool = False) -> ModelRecord:
        target = Path(path)
        if not target.exists():
            return ModelRecord(target, self._kind(target), issues=[ModelIssue("ERROR", "file does not exist")])
        record = self._base_record(target) if not _hash_already_computed else self._base_record(target)
        if not record.valid:
            return record
        if self.trusted_models_only and self._expected_hash(target.name) != record.sha256:
            record.issues.append(ModelIssue("ERROR", "refusing torch.load for an untrusted checkpoint"))
            return record
        try:
            import torch
        except ImportError:
            record.issues.append(ModelIssue("ERROR", "torch is not installed; checkpoint internals could not be validated"))
            return record
        try:
            checkpoint = torch.load(target, map_location="cpu", weights_only=False)
        except Exception as exc:
            record.issues.append(ModelIssue("ERROR", f"checkpoint could not be read: {exc}"))
            return record
        if record.kind == "detector":
            model = checkpoint.get("model") if isinstance(checkpoint, dict) else checkpoint
            names = getattr(model, "names", None) or (checkpoint.get("names") if isinstance(checkpoint, dict) else None)
            if names is not None:
                actual = [names[i] for i in range(len(names))] if isinstance(names, dict) else list(names)
                record.metadata["classes"] = actual
                if actual != EXPECTED_CLASSES:
                    record.issues.append(ModelIssue("ERROR", "detector class names do not match the 21-class contract"))
            else:
                record.issues.append(ModelIssue("WARNING", "detector class names were not found in checkpoint"))
        elif record.kind == "reid":
            cfg = checkpoint.get("cfg") if isinstance(checkpoint, dict) else None
            state = checkpoint.get("state_dict") if isinstance(checkpoint, dict) else None
            if not isinstance(cfg, dict) or cfg.get("backbone") != "resnet50" or tuple(cfg.get("size", ())) != (224, 224):
                record.issues.append(ModelIssue("ERROR", "ReID cfg must declare resnet50 and size (224, 224)"))
            keys = set(state or {})
            if not any(k.startswith("backbone.") for k in keys) or not any(k.startswith(("bn.", "bnneck.")) for k in keys):
                record.issues.append(ModelIssue("ERROR", "ReID checkpoint must contain backbone and BNNeck weights"))
        else:
            # reid_attribute or other auxiliary models
            pass
        return record
