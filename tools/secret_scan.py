"""Small CI secret scanner; never prints matched secret values."""
from __future__ import annotations

import re
import sys
from pathlib import Path

PATTERNS = (
    re.compile(r"KGAT_[A-Za-z0-9]+"),
    re.compile(r"(?:sk|ghp|github_pat)_[A-Za-z0-9_-]{12,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"(?:KAGGLE_KEY|ROBOFLOW_API_KEY)\s*[:=]\s*[\"'][^\"']+[\"']"),
    re.compile(r"-----BEGIN (?:RSA|OPENSSH|EC|DSA|PRIVATE) KEY-----"),
)
EXCLUDED_PARTS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules"}
EXCLUDED_NAMES = {"secret_scan.py"}
TEXT_SUFFIXES = {".py", ".md", ".yaml", ".yml", ".json", ".toml", ".txt", ".ipynb", ".cfg", ".ini", ".env"}


def scan(root: Path) -> list[tuple[Path, int]]:
    findings: list[tuple[Path, int]] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.name in EXCLUDED_NAMES or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if EXCLUDED_PARTS.intersection(path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            if any(pattern.search(line) for pattern in PATTERNS):
                findings.append((path.relative_to(root), line_no))
    return findings


def main() -> int:
    findings = scan(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd())
    for path, line_no in findings:
        print(f"potential secret: {path}:{line_no}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
