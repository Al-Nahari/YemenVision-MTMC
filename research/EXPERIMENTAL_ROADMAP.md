# الخطة التجريبية — Phase 01 إلى هندسة البيانات

## 0. قواعد التجارب
- preregister protocol/config قبل رؤية test results.
- train/validation/test مفصولة حسب الهوية والكاميرا والزمن.
- يمنع frame-neighbor leakage عبر split عشوائي.
- كل تشغيل يسجل commit، config، seed، environment probe، data hash، model hash، logs، metrics.
- test المحلي مغلق حتى نهاية التجربة.
- أي association بين الكاميرات احتمالي ومحدود الغرض والمدة.

## 1. بوابات التنفيذ

### Gate A — Data and license readiness
**Inputs:** release manifests، license texts، local authorization، data card.  
**Pass:** كل dataset له source/version/hash/license status؛ local data collection approved.  
**Fail action:** لا تنزيل/تدريب production؛ استخدم synthetic fixtures أو public research-only data.

### Gate B — Reproducible environment
**Pass:** environment probe وlock file وsmoke imports وseed test.  
**Measurement:** exact OS/Python/GPU/CUDA/packages.

### Gate C — Single-camera baseline
**Experiments:** detector × tracker، three seeds حيث يلزم.  
**Metrics:** detection mAP/recall/latency؛ tracking HOTA/MOTA/IDF1/IDs/FPS.  
**Deliverable:** benchmark table + error taxonomy.

### Gate D — ReID baseline
**Experiments:** CNN → TransReID، source-only ثم local fine-tune.  
**Metrics:** mAP، Rank-1/5/10، cross-camera mAP، false match at operating thresholds.  
**Leakage check:** identity-disjoint split.

### Gate E — MTMC association
**Ablations:** appearance; appearance+time; appearance+topology; full fusion; graph/GNN optional.  
**Metrics:** MTMC IDF1/HOTA/ID switches، pairwise precision/recall/AP، abstention coverage.  
**Safety:** TTL، role permissions، no unrestricted identity history.

### Gate F — Domain adaptation
**Protocols:** source-only، supervised small target، weak adaptation، augmentation.  
**Metrics:** target gain، source regression، calibration، subgroup/environment breakdown.  
**Pass:** improvement reproducible on held-out time/camera.

### Gate G — Analytics validity
**Tasks:** line crossing، zone count، direction، travel-time، density.  
**Metrics:** count MAE/RMSE، directional F1، queue-length error، calibration coverage.  
**Requirement:** camera calibration and uncertainty.

## 2. Ablation matrix
| ID | Detector | Tracker | ReID | Temporal | Topology | Purpose |
|---|---|---|---|---|---|---|
| A0 | fixed baseline | SORT | none | no | no | lower bound |
| A1 | fixed baseline | ByteTrack | none | no | no | tracker effect |
| A2 | fixed baseline | ByteTrack | CNN | no | no | appearance effect |
| A3 | fixed baseline | ByteTrack | CNN | yes | no | temporal effect |
| A4 | fixed baseline | ByteTrack | CNN | yes | yes | topology effect |
| A5 | fixed baseline | BoT-SORT | CNN | yes | yes | tracker alternative |
| A6 | fixed baseline | ByteTrack | TransReID | yes | yes | ReID model effect |
| A7 | fixed baseline | ByteTrack | DINOv2 | yes | yes | generic feature ablation |

## 3. Expected artifacts per run
- `config.yaml`
- `environment_probe.json`
- `data_manifest.json`
- `metrics.json`
- `predictions/` with restricted access
- `error_taxonomy.md`
- `model_card.md` update
- `experiment_report.md`
- `repro_command.txt`

## 4. Minimal local pilot
1. اجمع 2–4 كاميرات مصرح بها، فترات زمنية متباعدة، بعد redaction policy.
2. علّم subset detection/class/type/tracklet، ولا تستخدم plate text كهوية.
3. أنشئ train/val/test زمنيًا وهوويًا.
4. شغّل detector+ByteTrack وmanual review.
5. أضف ReID وassociation على test مغلق.
6. راجع false matches وabstentions قبل أي dashboard.

## 5. Acceptance thresholds to define after pilot
لا نضع أرقامًا ثابتة من الأدبيات. يحدد مالك المنتج بعد pilot:
- minimum recall per critical vehicle class.
- maximum ID switch rate.
- minimum cross-camera precision at selected coverage.
- maximum p95 latency and VRAM.
- maximum retention and access surface.

## 6. Next phase entry checklist
- [ ] local authorization and privacy review complete.
- [ ] public dataset licenses verified for intended use.
- [ ] camera inventory and topology schema approved.
- [ ] annotation guideline and QA sampling ready.
- [ ] data versioning/storage/access policy ready.
- [ ] baseline environment captured.
