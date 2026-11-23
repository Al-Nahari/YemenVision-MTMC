"""Small, dependency-free secret scan for CI.

This is intentionally conservative: it only looks for unmistakable credential
formats (private keys and well-known token prefixes), so documentation and
``.env.example`` placeholders do not create noise. It is not a replacement for
a managed secret scanner or secret manager.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SKIP_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "node_modules", "dist", "build",
    "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", ".angular",
}
SKIP_SUFFIXES = {
    ".pt", ".pth", ".bin", ".onnx", ".engine", ".tflite", ".weights", ".mp4",
    ".avi", ".mkv", ".mov", ".png", ".jpg", ".jpeg", ".gif", ".zip", ".pdf",
    ".ico", ".woff", ".woff2", ".ttf", ".db", ".sqlite", ".sqlite3",
}
PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    "OpenAI key": re.compile(r"sk-[A-Za-z0-9]{32,}"),
    "Slack token": re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
}


def scan(root: Path) -> list[str]:
    findings: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() in SKIP_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            for label, pattern in PATTERNS.items():
                if pattern.search(line):
                    findings.append(f"{path.relative_to(root)}:{line_number}: possible {label}")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args(argv)
    findings = scan(Path(args.root).resolve())
    if findings:
        print("Potential secrets found:", file=sys.stderr)
        for finding in findings:
            print(f"  {finding}", file=sys.stderr)
        return 1
    print("secret scan: no credential patterns found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
