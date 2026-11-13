# Phase 04 status — Multi-object tracking

## Implemented

- A detector-agnostic `Detector` interface and camera/video-local event schema.
- A runnable constant-velocity, IoU-gated baseline with initialization, tentative confirmation, prediction, association, loss, reactivation, termination and duplicate suppression.
- Video diagnostics: boxes, local track IDs, trajectory lines, class, confidence and lifecycle state.
- JSONL event records and processing-FPS report.
- TrackEval runner for official HOTA, CLEAR (MOTA/ID switches) and Identity (IDF1) metrics.

## Evidence state

No video, ground truth, trained detector, or tracker experiment is present in the supplied workspace. Numeric evaluation and an algorithm-selection decision are therefore **pending approved independent video data**. IDs emitted by this phase are explicitly local to `(camera_id, video_id)` and never claim cross-camera identity.
