"""Safe, resumable downloads gated by an explicit verified manifest."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DownloadSpec:
    """A download declaration requiring an approved source and known hash."""

    dataset: str
    release: str
    url: str
    destination: Path
    sha256: str
    license_status: str
    approved_for_download: bool = False

    def validate(self) -> None:
        """Reject unsafe or incomplete specifications before network access."""
        parsed = urlparse(self.url)
        if parsed.scheme not in {"https"}:
            raise ValueError("Only HTTPS sources are allowed")
        if not self.sha256 or len(self.sha256) != 64:
            raise ValueError("A 64-character SHA-256 hash is required")
        if self.license_status != "verified":
            raise PermissionError("License status must be verified before download")
        if not self.approved_for_download:
            raise PermissionError("Download requires explicit approval in the manifest")


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Hash a local file incrementally."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resumable_download(spec: DownloadSpec, retries: int = 3, timeout: int = 60) -> dict[str, str | int]:
    """Download a verified artifact with HTTP range resume and atomic replacement."""
    spec.validate()
    destination = spec.destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            offset = partial.stat().st_size if partial.exists() else 0
            headers = {"User-Agent": "YemenVision-MTMC/phase02"}
            if offset:
                headers["Range"] = f"bytes={offset}-"
            request = Request(spec.url, headers=headers)
            with urlopen(request, timeout=timeout) as response, partial.open("ab" if offset else "wb") as handle:
                if offset and response.status != 206:
                    LOGGER.warning("Server ignored resume range; restarting download")
                    offset = 0
                    handle.close()
                    partial.unlink(missing_ok=True)
                    continue
                while chunk := response.read(1024 * 1024):
                    handle.write(chunk)
            actual_hash = sha256_file(partial)
            if actual_hash != spec.sha256.lower():
                raise ValueError(f"SHA-256 mismatch: expected {spec.sha256}, got {actual_hash}")
            partial.replace(destination)
            return {
                "dataset": spec.dataset,
                "release": spec.release,
                "destination": str(destination),
                "sha256": actual_hash,
                "downloaded_at_utc": datetime.now(UTC).isoformat(),
                "attempts": attempt,
            }
        except Exception as exc:  # Retry only after recording the failure.
            last_error = exc
            LOGGER.warning("Download attempt %s/%s failed: %s", attempt, retries, exc)
            if attempt < retries:
                time.sleep(min(2**attempt, 8))
    raise RuntimeError(f"Download failed after {retries} attempts") from last_error


def load_manifest(path: Path) -> list[DownloadSpec]:
    """Load explicit download specs from a JSON manifest."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("Download manifest must be a JSON list")
    return [DownloadSpec(destination=Path(item.pop("destination")), **item) for item in raw]
