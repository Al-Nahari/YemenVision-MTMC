# Model artifacts

Place user-provided weights in this directory (or set `YV_MODELS_DIR`). Weight files are read-only and are not committed to git.

## Current local status (2026-11-22)

> **ReID is not usable in this checkout.** `models/reid_best.pt` is a truncated
> archive (it starts with `PK` but has no ZIP central directory). `yv check-models`
> reports it as revoked/ERROR and the backend must refuse to load it.
>
> `detector_best.pt` is a complete ZIP archive and matches `manifest.json`.
> Loading it still requires a working OpenCV runtime.
>
> Do not report ReID or MTMC metrics until a verified `reid_best.pt` is restored.

## Production models (stage5 — 2026-11-18)

- `detector_best.pt`: YOLOv11m detector fine-tuned on COCO, 21 vehicle classes.
  - Recommended inference: `imgsz=800`, `conf=0.55`, `iou=0.6`, TTA enabled.
- `reid_best.pt`: ResNet50 + AdaptiveAvgPool + BNNeck, 2048-dimensional inference embedding.
  - Architecture: ReIDNetV2 (last_stride, pool type stored in checkpoint cfg).
  - **Status: revoked locally — truncated artifact.**
- `vehicle_attributes.pt`: Vehicle attribute model (not used for production ReID inference).

## Expected inference artifacts

- `detector_best.pt` or `best.pt` or `detection_yolo11s_best.pt`: default YOLO detector, 21 classes.
- `detector_finetuned_<RUN>_best.pt`: selectable comparison detector, never the default.
- `reid_best.pt` or `reid_bot_best.pt`: ResNet50 + AdaptiveAvgPool + BNNeck, 2048-dimensional inference embedding.
- `*_last.pt`: training-resume checkpoints; rejected for inference.
- `reid_attr_*` / `vehicle_attributes.pt`: attribute checkpoints; rejected for production ReID inference.

## Validation

`manifest.json` maps filenames to approved SHA-256 hashes and may revoke a file
by name. Both manifests agree on the promoted ReID hash
(`956b55a30585f89859d02524e44b7f73bd53362f871f0b098f0badf1fd756c18`); the local
truncated copy has a different observed hash and stays revoked. Run
`yv check-models` after adding artifacts. The command never downloads weights
and never modifies them. See `docs/MODELS.md` for the full contract.
