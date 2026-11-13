"""Reproducible Ultralytics training wrapper with resume/checkpoint support."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import yaml
from .validate import load_contract

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True); p.add_argument("--config", default="configs/detection_yolo11n.yaml")
    p.add_argument("--model"); p.add_argument("--name", required=True); p.add_argument("--project", default="runs/detect")
    p.add_argument("--resume", action="store_true"); args = p.parse_args()
    contract = load_contract(args.data)
    with open(args.config, encoding="utf-8") as f: cfg = yaml.safe_load(f) or {}
    from ultralytics import YOLO
    model = YOLO(args.model or cfg.pop("model"))
    augment = cfg.pop("augment", {})
    # Unsupported transforms are logged but never silently applied.
    unsupported = {k: augment.pop(k) for k in list(augment) if k in {"blur_probability", "weather_probability"}}
    Path(args.project, args.name).mkdir(parents=True, exist_ok=True)
    Path(args.project, args.name, "run_config.json").write_text(json.dumps({"config": cfg, "augment": augment, "not_applied": unsupported, "classes": contract["names"]}, indent=2), encoding="utf-8")
    model.train(data=args.data, project=args.project, name=args.name, resume=args.resume, save=True, **cfg, **augment)
if __name__ == "__main__": main()
