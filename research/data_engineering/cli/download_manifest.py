"""Download only entries explicitly approved in a verified manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..acquisition import load_manifest, resumable_download


def main() -> None:
    """Execute approved downloads and write a provenance log."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--provenance", type=Path, required=True)
    args = parser.parse_args()

    results = [resumable_download(spec) for spec in load_manifest(args.manifest)]
    args.provenance.parent.mkdir(parents=True, exist_ok=True)
    args.provenance.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Downloaded {len(results)} approved artifact(s)")


if __name__ == "__main__":
    main()
