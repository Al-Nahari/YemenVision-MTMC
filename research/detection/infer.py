"""Image, directory, batch, or video inference with configurable confidence."""
from __future__ import annotations
import argparse
from pathlib import Path
def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--weights", required=True); p.add_argument("--source", required=True)
    p.add_argument("--output", default="runs/inference"); p.add_argument("--conf", type=float, default=0.25); p.add_argument("--imgsz", type=int, default=960)
    a = p.parse_args(); assert 0 <= a.conf <= 1, "--conf must be in [0, 1]"
    from ultralytics import YOLO
    Path(a.output).mkdir(parents=True, exist_ok=True)
    YOLO(a.weights).predict(source=a.source, conf=a.conf, imgsz=a.imgsz, save=True, project=a.output, name="predictions", exist_ok=True)
if __name__ == "__main__": main()
