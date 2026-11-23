"""Application settings loaded from environment and an optional local .env file."""
import logging
import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# Load backend/.env regardless of whether Uvicorn is launched from repo root or backend/.
if load_dotenv:
    load_dotenv(Path(__file__).resolve().parents[1] / '.env', override=False)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {'1', 'true', 'yes', 'on'}:
        return True
    if normalized in {'0', 'false', 'no', 'off'}:
        return False
    raise ValueError(f'{name} must be a boolean, got {value!r}')


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def _env_list(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if value is None:
        return default
    return [item.strip() for item in value.split(',') if item.strip()]


def _default_models_dir() -> Path:
    """Resolve the repository ``models/`` directory for local runs.

    In the container the app lives at ``/app/app/config.py``, so this also
    resolves to ``/models`` where docker-compose mounts the read-only weights.
    An explicit ``YV_MODELS_DIR`` always wins.
    """
    configured = os.getenv('YV_MODELS_DIR')
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / 'models'


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv('DATABASE_URL', 'sqlite:///./traffic_platform.db')
    api_keys_json: str = os.getenv('API_KEYS_JSON', '{}')
    rate_limit_per_minute: int = _env_int('RATE_LIMIT_PER_MINUTE', 120)
    retention_days: int = _env_int('RETENTION_DAYS', 30)

    models_dir: Path = field(default_factory=_default_models_dir)
    trusted_models_only: bool = _env_bool('YV_TRUSTED_MODELS_ONLY', True)

    max_upload_bytes: int = _env_int('YV_MAX_UPLOAD_BYTES', 500 * 1024 * 1024)
    cors_origins: list[str] = field(
        default_factory=lambda: _env_list(
            'YV_CORS_ORIGINS',
            ['http://localhost:4200', 'http://127.0.0.1:4200'],
        )
    )

    # Media URLs are HMAC-signed so the processed-videos directory is never
    # exposed as an unauthenticated static mount. Set this in production.
    media_signing_key: str = os.getenv('MEDIA_SIGNING_KEY', '')
    media_url_ttl_seconds: int = _env_int('MEDIA_URL_TTL_SECONDS', 3600)

    # The dashboard now records plate numbers in the data logs, so the stored
    # video is intentionally unblurred by default. Set YV_PRIVACY_BLUR_PLATES=true
    # and a blur mode if a deployment needs redacted output instead.
    blur_plates: bool = _env_bool('YV_PRIVACY_BLUR_PLATES', False)
    allow_unblurred_output: bool = _env_bool('YV_PRIVACY_ALLOW_UNBLURRED', True)
    # plate_region: blur the lower part of each vehicle box (heuristic until a
    # dedicated plate detector is wired in). vehicle: blur the whole vehicle box.
    blur_mode: str = os.getenv('YV_PRIVACY_BLUR_MODE', 'off').strip().lower()

    # CPU budget knobs. Keeping inference resolution bounded is the single
    # biggest win on weak machines; OCR is throttled and lazy-loaded.
    max_infer_width: int = _env_int('YV_MAX_INFER_WIDTH', 960)
    plate_ocr_enabled: bool = _env_bool('YV_PLATE_OCR_ENABLED', True)
    plate_ocr_interval_frames: int = _env_int('YV_PLATE_OCR_INTERVAL', 30)
    plate_ocr_max_per_frame: int = _env_int('YV_PLATE_OCR_MAX_PER_FRAME', 4)
    plate_ocr_min_confidence: float = float(os.getenv('YV_PLATE_OCR_MIN_CONFIDENCE', '0.55'))

    def __post_init__(self) -> None:
        if self.blur_mode not in {'plate_region', 'vehicle', 'off'}:
            raise ValueError("YV_PRIVACY_BLUR_MODE must be 'plate_region', 'vehicle', or 'off'")
        if self.blur_plates and self.blur_mode == 'off':
            raise ValueError('blur_plates is enabled but blur_mode is off; choose plate_region or vehicle')
        if not self.blur_plates and not self.allow_unblurred_output:
            raise ValueError('unblurred output requires YV_PRIVACY_ALLOW_UNBLURRED=true')
        if self.max_upload_bytes < 1:
            raise ValueError('YV_MAX_UPLOAD_BYTES must be positive')
        if self.max_infer_width < 160:
            raise ValueError('YV_MAX_INFER_WIDTH must be at least 160')
        if self.plate_ocr_interval_frames < 1 or self.plate_ocr_max_per_frame < 1:
            raise ValueError('plate OCR interval and per-frame limit must be positive')
        if self.media_url_ttl_seconds < 1:
            raise ValueError('MEDIA_URL_TTL_SECONDS must be positive')
        if not self.media_signing_key:
            # Development-only fallback. Tokens stop working after a restart and
            # are not shared between worker processes. Production must set
            # MEDIA_SIGNING_KEY explicitly.
            logging.getLogger(__name__).warning(
                'MEDIA_SIGNING_KEY is unset; using a process-local development key'
            )
            object.__setattr__(self, 'media_signing_key', secrets.token_urlsafe(32))


settings = Settings()
