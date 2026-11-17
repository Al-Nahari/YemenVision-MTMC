# Evaluation policy

Metrics are produced only by executing against an identified dataset manifest and model hash. No reference number is copied into a result artifact as a measured value.

## Current evidence

- Detection: **NOT_EVALUATED in this checkout**; no weights or validation images are present.
- ReID: **NOT_EVALUATED**; no VeRi query/gallery files or weights are present.
- Association: **NOT_EVALUATED**; no synchronized camera tracklets or identity ground truth are present.
- MOT: **NOT_EVALUATED**; no MOTChallenge sequences are present.
- End-to-end video: **NOT_EVALUATED**; no video, OpenCV, or detector runtime is present.

## Required protocol

- Detection: Ultralytics validation on the private validation set and COCO subset when present.
- ReID: VeRi query/gallery with identity-leakage checks, mAP and CMC.
- Association: dev threshold selection followed by eval IDF1/pairwise-F1/ARI.
- MOT: `motmetrics` only when MOT ground truth is present.
- Official MTMC: `NOT_EVALUATED` until synchronized multi-camera video and identity ground truth exist.

The numbers in the original research prompt are reference targets only. A large difference requires investigation of preprocessing, class order, split, and checkpoint compatibility; it is never silently normalized.
