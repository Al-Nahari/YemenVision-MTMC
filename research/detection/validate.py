"""Fail-fast validation for a YOLO-format detection dataset."""
from __future__ import annotations
import argparse, csv
from pathlib import Path
import yaml

def load_contract(path: str) -> dict:
    contract_path = Path(path).resolve()
    with contract_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    root = Path(data.get("path", "")).expanduser()
    if not root.is_absolute(): root = (contract_path.parent / root).resolve()
    names = data.get("names") or {}
    names = list(names.values()) if isinstance(names, dict) else names
    if not root.exists(): raise ValueError(f"Dataset root does not exist: {root}")
    if not names: raise ValueError("names must be declared from approved labelled data")
    if len(names) != len(set(names)): raise ValueError("Class names must be unique")
    for split in ("train", "val", "test"):
        item = data.get(split)
        if not item: raise ValueError(f"Missing '{split}' split")
        image_dir = root / item
        if not image_dir.exists(): raise ValueError(f"Missing split directory: {image_dir}")
    return {"root": root, "names": names, "data": data}

def verify_manifest(manifest: str) -> None:
    seen, groups = set(), {}
    with Path(manifest).open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            required = {"image", "split", "domain", "group_id"}
            if not required.issubset(row): raise ValueError("Manifest needs image, split, domain, group_id columns")
            if row["image"] in seen: raise ValueError(f"Duplicate image: {row['image']}")
            seen.add(row["image"])
            groups.setdefault(row["group_id"], set()).add(row["split"])
    leaked = [k for k, v in groups.items() if len(v) > 1]
    if leaked: raise ValueError(f"Group leakage across splits: {leaked[:5]}")

def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--data", required=True); args = p.parse_args()
    c = load_contract(args.data)
    manifest = c["data"].get("split_manifest")
    if manifest:
        if not Path(manifest).exists(): raise ValueError(f"Manifest missing: {manifest}")
        verify_manifest(manifest)
    print({"status": "READY_FOR_TRAINING", "classes": c["names"], "root": str(c["root"])})
if __name__ == "__main__": main()
