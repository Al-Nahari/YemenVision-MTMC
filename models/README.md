# Model artifacts

Place user-provided weights in this directory (or set `YV_MODELS_DIR`). Weight files are read-only and are not committed to git.

## Production models (stage5 — 2026-11-18)

- `detector_best.pt`: YOLOv11m detector fine-tuned on COCO, 21 vehicle classes.
  - Recommended inference: `imgsz=800`, `conf=0.55`, `iou=0.6`, TTA enabled.
- `reid_best.pt`: ResNet50 + AdaptiveAvgPool + BNNeck, 2048-dimensional inference embedding.
  - Architecture: ReIDNetV2 (last_stride, pool type stored in checkpoint cfg).
- `vehicle_attributes.pt`: Vehicle attribute model (not used for production ReID inference).

## Expected inference artifacts

- `detector_best.pt` or `best.pt` or `detection_yolo11s_best.pt`: default YOLO detector, 21 classes.
- `detector_finetuned_<RUN>_best.pt`: selectable comparison detector, never the default.
- `reid_best.pt` or `reid_bot_best.pt`: ResNet50 + AdaptiveAvgPool + BNNeck, 2048-dimensional inference embedding.
- `*_last.pt`: training-resume checkpoints; rejected for inference.
- `reid_attr_*` / `vehicle_attributes.pt`: attribute checkpoints; rejected for production ReID inference.

## Validation

Optional `manifest.json` maps filenames to approved SHA-256 hashes. Run `yv check-models` after adding artifacts. The command never downloads weights and never modifies them.
