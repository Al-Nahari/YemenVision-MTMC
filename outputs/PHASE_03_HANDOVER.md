# Phase 03 handover

## Delivered

The Phase 03 vehicle-detection engine is implemented in `research/detection/` with dataset validation, YOLO and RT-DETR configurations, reproducible training, evaluation, inference, ONNX/TensorRT export, and parity validation. Four requested notebooks are in `research/notebooks/`.

## Current measured result

None. The supplied archive contains no approved images, annotations, split manifest, or weights. Its own Phase 02 provenance explicitly lists no downloaded files. Accordingly, no trained model, score, latency, FPS, GPU-memory figure, exported model, or demo video has been fabricated.

## Operational handoff

1. Copy `research/configs/detection_data.example.yaml` to a non-template dataset YAML and enter only approved paths/classes.
2. Create the camera/video-grouped manifest and run `python -m detection.validate --data <yaml>` from `research`.
3. Install `requirements-phase03.txt`, run the YOLO baseline, then the RT-DETR comparator using the same independent test protocol.
4. Evaluate public and Yemen-local test sets separately, then export the selected checkpoint and retain its parity report.

The next acceptance decision must be based on the first measured baseline; no accuracy target has been preset.
