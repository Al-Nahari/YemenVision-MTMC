"""Application settings loaded from environment and an optional local .env file."""
import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# Load backend/.env regardless of whether Uvicorn is launched from repo root or backend/.
if load_dotenv:
    load_dotenv(Path(__file__).resolve().parents[1] / '.env', override=False)


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv('DATABASE_URL', 'sqlite:///./traffic_platform.db')
    api_keys_json: str = os.getenv('API_KEYS_JSON', '{}')
    rate_limit_per_minute: int = int(os.getenv('RATE_LIMIT_PER_MINUTE', '120'))
    retention_days: int = int(os.getenv('RETENTION_DAYS', '30'))


settings = Settings()
