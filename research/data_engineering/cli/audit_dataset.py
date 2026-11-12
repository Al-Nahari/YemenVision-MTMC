"""Run a JSONL unified-schema quality audit from the command line."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..adapters import create_adapter
from ..quality import validate_records, write_json_report


def main() -> None:
    """Parse arguments, normalize records, and write a quality report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, help="Registered adapter name")
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--release", required=True)
    parser.add_argument("--annotations", default="annotations.jsonl")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    adapter = create_adapter(args.dataset, args.source_root, args.release, args.annotations)
    report = validate_records(adapter.iter_records())
    report["dataset"] = adapter.dataset_name
    report["release"] = args.release
    write_json_report(report, args.output)
    print(json.dumps({"output": str(args.output), "record_count": report["record_count"]}))


if __name__ == "__main__":
    main()
