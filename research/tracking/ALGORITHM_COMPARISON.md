# Tracking algorithm comparison plan

## Candidates

| Algorithm | Association | Appearance | Best hypothesis | Risk / tuning focus |
|---|---|---|---|---|
| ByteTrack | high- and low-confidence detections + motion | no | speed and recall under detector score drops | confidence thresholds, buffer |
| BoT-SORT | motion/IoU; optional GMC | optional ReID | moving camera or moderate occlusion | GMC/ReID cost and calibration |
| OC-SORT | observation-centric motion | no | non-linear motion and short occlusions | observation update / max-age |
| DeepSORT / StrongSORT | Kalman + appearance distance | yes | long occlusions where vehicles are visually distinct | appearance drift, VRAM and latency |

Appearance features can reduce ID switches after occlusion only when crops are sufficiently resolved and the embedding is domain-aligned. They can degrade association for visually similar vehicles, tiny/dark crops, viewpoint change, or poor calibration; therefore compare appearance-on/off on the same detections.

## Baseline decision rule

Run official TrackEval separately for public and Yemen-local held-out videos. Compare HOTA (primary), IDF1, MOTA, ID switches, fragmentation, mostly tracked/lost, completeness and processing FPS. The approved Phase 04 baseline is **pending measurement**; do not promote any algorithm before the same-video, same-detector comparison.

## Parameters to record

Detector confidence, IoU/motion gate, match threshold, `min_hits`, `max_lost`/track buffer, Kalman process/measurement noise, frame rate, input resolution, ReID model/version and threshold, seed, GPU, and code revision.
