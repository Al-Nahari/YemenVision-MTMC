"""Export ONNX/TensorRT when supported; record post-export numerical parity."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--weights", required=True); p.add_argument("--format", choices=["onnx", "engine"], default="onnx")
    p.add_argument("--sample", required=True, help="Representative approved image for parity check"); p.add_argument("--imgsz", type=int, default=960); p.add_argument("--atol", type=float, default=1e-3)
    a = p.parse_args()
    from ultralytics import YOLO
    model = YOLO(a.weights); exported = model.export(format=a.format, imgsz=a.imgsz)
    native = model.predict(a.sample, imgsz=a.imgsz, verbose=False)[0]
    exported_result = YOLO(exported).predict(a.sample, imgsz=a.imgsz, verbose=False)[0]
    native_boxes, export_boxes = native.boxes.xyxy.cpu().numpy(), exported_result.boxes.xyxy.cpu().numpy()
    # Counts must match. Coordinates are compared only in the stable common prefix.
    count_match = len(native_boxes) == len(export_boxes)
    max_abs = float(np.max(np.abs(native_boxes[:min(len(native_boxes),len(export_boxes))] - export_boxes[:min(len(native_boxes),len(export_boxes))]))) if min(len(native_boxes),len(export_boxes)) else 0.0
    result = {"exported": str(exported), "format": a.format, "sample": a.sample, "native_detections": len(native_boxes), "exported_detections": len(export_boxes), "count_match": count_match, "max_abs_xyxy": max_abs, "atol": a.atol, "passed": count_match and max_abs <= a.atol}
    Path(str(exported) + ".parity.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    if not result["passed"]: raise SystemExit("Export parity failed; inspect the recorded report")
    print(json.dumps(result, indent=2))
if __name__ == "__main__": main()
