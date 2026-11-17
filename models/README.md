# Model artifacts

Place user-provided weights in this directory (or set `YV_MODELS_DIR`). Weight files are read-only and are not committed to git.

Expected inference artifacts:

- `best.pt` or `detection_yolo11s_best.pt`: default YOLO11s detector, 21 classes.
- `detector_finetuned_<RUN>_best.pt`: selectable comparison detector, never the default.
- `reid_bot_best.pt`: ResNet50 + AdaptiveAvgPool + BNNeck, 2048-dimensional inference embedding.
- `*_last.pt`: training-resume checkpoints; rejected for inference.
- `reid_attr_*`: synthetic-attribute checkpoints; rejected for production inference.

Optional `manifest.json` maps filenames to approved SHA-256 hashes. Run `yv check-models` after adding artifacts. The command never downloads weights and never modifies them.
