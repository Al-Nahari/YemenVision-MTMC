# Phase 03 benchmark protocol

All candidates use identical approved class taxonomy, split manifests, input resolution, hardware, batch, precision, confidence threshold, and three seeds where practical. Measure after warm-up; never compare one-off inference times.

| Candidate | Role | Starting configuration | Decision metric |
|---|---|---|---|
| YOLO11n | reproducible speed baseline | `configs/detection_yolo11n.yaml` | mAP50-95, recall, p50/p95 latency, FPS, VRAM |
| YOLO11s/m | capacity scaling | same schedule, resolution sweep (640/960/1280) | error reduction versus cost |
| RT-DETR-L | crowded-scene accuracy comparator | `configs/detection_rtdetr_l.yaml` | same metrics, small-object and crowd slices |

Report per-class AP plus public and Yemen-local results in separate tables. A model advances only if it improves an agreed primary metric without unacceptable recall, latency, memory, or local-domain regression. No numerical target is set before the first measured baseline.
