# Phase 03 status — Vehicle Detection & Classification

## Evidence state: BLOCKED_PENDING_APPROVED_DATA

The delivered archive includes engineering scaffolding only. `research/data/manifests/provenance.json` says `downloaded_files: []`, and `PHASE_02_DATA_READINESS_REPORT.md` states `CONDITIONAL / NOT_READY_FOR_TRAINING`. Therefore this phase contains no fabricated trained model, scores, benchmark comparison, exported model, or demo video.

## Implemented now

- Dataset-contract and leakage validator (`python -m detection.validate`).
- Reproducible YOLO baseline runner with AMP, AdamW, warmup, weight decay, scheduling, augmentation settings, checkpointing and resume.
- Evaluation runner that retains PR/confusion artifacts produced by the backend.
- Image/batch/video inference API and configurable confidence threshold.
- ONNX or TensorRT-engine export path with a recorded parity gate.
- Four execution notebooks and a model card.

## Required next gate

1. Obtain written authorization/licensing and provenance for data.
2. Create immutable train/val/test manifests grouped by camera/video; hold out Yemen-local data independently.
3. Fill class names from annotated data and run `detection.validate`.
4. Establish a measured YOLO baseline, then compare RT-DETR on the same split, hardware, precision, resolution, and threshold.
5. Set improvement targets only after that baseline and complete export parity testing.
