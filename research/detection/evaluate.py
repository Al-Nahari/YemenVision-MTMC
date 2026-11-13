"""Evaluate a checkpoint and persist machine-readable, reproducible metrics."""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import torch
from .validate import load_contract

def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--weights", required=True); p.add_argument("--data", required=True)
    p.add_argument("--split", default="test", choices=["val", "test"]); p.add_argument("--imgsz", type=int, default=960); p.add_argument("--output", default="reports/evaluation")
    a = p.parse_args(); contract = load_contract(a.data); out = Path(a.output); out.mkdir(parents=True, exist_ok=True)
    from ultralytics import YOLO
    model = YOLO(a.weights)
    started = time.perf_counter()
    metrics = model.val(data=a.data, split=a.split, imgsz=a.imgsz, plots=True, project=str(out), name="artifacts", exist_ok=True)
    elapsed = time.perf_counter() - started
    results = getattr(metrics, "results_dict", {})
    report = {"weights": a.weights, "data": a.data, "split": a.split, "classes": contract["names"], "metrics": results, "wall_seconds": elapsed,
              "required_artifacts": ["PR_curve.png", "confusion_matrix.png", "confusion_matrix_normalized.png"],
              "note": "Report applies to the requested split. Run separately for approved public and Yemen-local split YAMLs; do not aggregate them."}
    (out / "metrics.json").write_text(json.dumps(report, indent=2, default=float), encoding="utf-8")
    print(json.dumps(report, indent=2, default=float))
if __name__ == "__main__": main()
