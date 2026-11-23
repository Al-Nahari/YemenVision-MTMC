"""HMAC-signed media URLs.

Processed videos are personal data. They must not be exposed through an
unauthenticated ``StaticFiles`` mount. The API returns a short-lived signed
URL instead, and the media endpoint verifies the signature before serving.
"""
from __future__ import annotations

import hashlib
import hmac
import time
from pathlib import Path
from urllib.parse import quote

from app.config import settings

MEDIA_ROUTE = '/api/v1/media'


def _signature(name: str, expires: int) -> str:
    message = f'{name}:{expires}'.encode()
    return hmac.new(settings.media_signing_key.encode('utf-8'), message, hashlib.sha256).hexdigest()


def media_url(name: str, ttl_seconds: int | None = None) -> str:
    """Return a relative signed URL for a file in the processed-videos directory."""
    safe_name = Path(name).name
    expires = int(time.time()) + (ttl_seconds or settings.media_url_ttl_seconds)
    signature = _signature(safe_name, expires)
    return f'{MEDIA_ROUTE}/{quote(safe_name)}?exp={expires}&sig={signature}'


def verify_media_request(name: str, expires: int, signature: str) -> bool:
    safe_name = Path(name).name
    if safe_name != name:
        return False
    if expires < int(time.time()):
        return False
    expected = _signature(safe_name, expires)
    return hmac.compare_digest(expected, signature)
