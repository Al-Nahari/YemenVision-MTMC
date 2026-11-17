from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from yemenvision.registry import ModelRegistry

def check_models(args: argparse.Namespace) -> int:
    registry = ModelRegistry(args.models_dir)
    records = registry.discover()
    print("kind\tstatus\tfilename\tsize_bytes\tsha256")
    errors = 0
    for record in records:
        print(f"{record.kind}\t{'OK' if record.valid else 'ERROR'}\t{record.path.name}\t{record.size_bytes}\t{record.sha256}")
        for issue in record.issues: print(f"  {issue.level}: {issue.message}")
        errors += int(not record.valid)
    if not records:
        print(f"NOT_EVALUATED\tno .pt files found in {registry.models_dir}")
        return 1
    return 1 if errors else 0

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="yv")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check-models"); check.add_argument("--models-dir", default=None); check.set_defaults(func=check_models)
    args = parser.parse_args(argv)
    return int(args.func(args))

if __name__ == "__main__": sys.exit(main())
