from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    if value.lower() in {"1", "true", "yes", "on"}:
        return True
    if value.lower() in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean, got {value!r}")


@dataclass(frozen=True)
class PrivacyConfig:
    blur_plates: bool = True
    keep_raw: bool = False
    allow_unblurred_output: bool = False


@dataclass(frozen=True)
class DetectionConfig:
    confidence: float = 0.55
    iou: float = 0.6
    imgsz: int = 800
    device: str = "auto"
    amp: bool = True


@dataclass(frozen=True)
class TrackingConfig:
    track_high_thresh: float = 0.25
    track_low_thresh: float = 0.1
    new_track_thresh: float = 0.25
    track_buffer: int = 50
    match_thresh: float = 0.8
    max_crops_per_tracklet: int = 8
    max_crop_memory_mb: int = 128


@dataclass(frozen=True)
class ReIDConfig:
    batch_size: int = 32
    crop_count: int = 8
    flip_tta: bool = True
    cache_dir: Path = Path("outputs/cache")


@dataclass(frozen=True)
class AssociationConfig:
    appearance_weight: float = 0.8
    spatiotemporal_weight: float = 0.2
    threshold: float = 0.5
    min_transition_seconds: float = 0.0
    max_transition_seconds: float = 3600.0
    allow_appearance_only: bool = False


@dataclass(frozen=True)
class Settings:
    models_dir: Path = Path("models")
    output_dir: Path = Path("outputs/runs")
    seed: int = 42
    privacy: PrivacyConfig = field(default_factory=PrivacyConfig)
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    tracking: TrackingConfig = field(default_factory=TrackingConfig)
    reid: ReIDConfig = field(default_factory=ReIDConfig)
    association: AssociationConfig = field(default_factory=AssociationConfig)

    def validate(self) -> Settings:
        if not 0 < self.detection.confidence <= 1 or not 0 < self.detection.iou <= 1:
            raise ValueError("detection confidence and iou must be in (0, 1]")
        if not 0 <= self.tracking.track_low_thresh <= self.tracking.track_high_thresh <= 1:
            raise ValueError("tracking thresholds must satisfy 0 <= low <= high <= 1")
        if self.reid.batch_size < 1 or self.reid.crop_count < 1:
            raise ValueError("ReID batch_size and crop_count must be positive")
        if not 0 <= self.association.appearance_weight <= 1:
            raise ValueError("association appearance_weight must be in [0, 1]")
        return self

    def as_dict(self) -> dict[str, Any]:
        return {
            "models_dir": str(self.models_dir), "output_dir": str(self.output_dir), "seed": self.seed,
            "privacy": self.privacy.__dict__, "detection": self.detection.__dict__,
            "tracking": self.tracking.__dict__, "reid": {**self.reid.__dict__, "cache_dir": str(self.reid.cache_dir)},
            "association": self.association.__dict__,
        }


def _section(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    if not isinstance(value, dict):
        raise ValueError(f"config.{key} must be a mapping")
    return dict(value)


def load_settings(path: str | Path | None = None, overrides: dict[str, Any] | None = None) -> Settings:
    """Load defaults, then YAML, then YV_* environment variables, then explicit overrides."""
    config_path = Path(path or os.getenv("YV_CONFIG", "configs/default.yaml"))
    data: dict[str, Any] = {}
    if config_path.exists():
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        if not isinstance(loaded, dict):
            raise ValueError(f"configuration root must be a mapping: {config_path}")
        data = loaded
    privacy = _section(data, "privacy")
    detection = _section(data, "detection")
    tracking = _section(data, "tracking")
    reid = _section(data, "reid")
    association = _section(data, "association")
    settings = Settings(
        models_dir=Path(os.getenv("YV_MODELS_DIR", data.get("models_dir", "models"))),
        output_dir=Path(os.getenv("YV_OUTPUT_DIR", data.get("output_dir", "outputs/runs"))),
        seed=int(os.getenv("YV_SEED", data.get("seed", 42))),
        privacy=PrivacyConfig(
            blur_plates=_env_bool("YV_PRIVACY_BLUR_PLATES", bool(privacy.get("blur_plates", True))),
            keep_raw=_env_bool("YV_PRIVACY_KEEP_RAW", bool(privacy.get("keep_raw", False))),
            allow_unblurred_output=_env_bool("YV_PRIVACY_ALLOW_UNBLURRED", bool(privacy.get("allow_unblurred_output", False))),
        ),
        detection=DetectionConfig(**detection), tracking=TrackingConfig(**tracking),
        reid=ReIDConfig(cache_dir=Path(reid.pop("cache_dir", "outputs/cache")), **reid),
        association=AssociationConfig(**association),
    )
    if overrides:
        # Explicit CLI overrides are intentionally limited to known top-level scalar values.
        for key, value in overrides.items():
            if key == "models_dir": settings = Settings(**{**settings.__dict__, "models_dir": Path(value)})
            elif key == "output_dir": settings = Settings(**{**settings.__dict__, "output_dir": Path(value)})
            else: raise ValueError(f"unsupported settings override: {key}")
    return settings.validate()
