# Model Benchmark Plan — YemenVision MTMC

## مبدأ المقارنة
لا توجد benchmark results محققة محليًا في هذه المرحلة. الجدول يحدد ما سيتم قياسه بنفس البيانات، detector، hardware، precision، batch، وseed.

## 1. Detection
| العائلة | نقاط القوة | الكلفة المتوقعة | مخاطر/قيود | خطة القياس |
|---|---|---|---|---|
| YOLO family | ecosystem ناضج، real-time، export متعدد | منخفضة إلى متوسطة حسب size | اختلاف licenses بين repo/weights، NMS وocclusion | mAP50-95، recall، small-object AP، latency/FPS، VRAM |
| RT-DETR | end-to-end transformer-style، مفاضلة decoder depth | متوسطة/عالية | يحتاج tuning وذاكرة أكبر غالبًا | نفس input/precision، مع/بدون NMS حسب implementation |
| detector baseline آخر | يختار بعد survey/availability | غير معروف | لا يُضاف بلا source/license | decision log |

**ترشيح:** YOLO small/medium baseline للسرعة، RT-DETR baseline للدقة/الازدحام. لا نثبت model size قبل `environment_probe`.

## 2. Single-camera Tracking
| النموذج | الفكرة | متوقع عمليًا | المخاطر |
|---|---|---|---|
| SORT | motion + Hungarian | أسرع baseline | ID switches مع occlusion |
| ByteTrack | يستفيد من low-score detections | strong simplicity/recall | sensitive to detector thresholds |
| BoT-SORT | appearance + GMC + motion | مناسب للـ occlusion/camera motion | tuning وembedding cost |
| OC-SORT | observation-centric motion | مفيد عند nonlinear motion/occlusion | لا يحل cross-camera identity وحده |
| StrongSORT | DeepSORT improvements | appearance أقوى محتملًا | heavier، dependency/checkpoint licensing |

**المقاييس:** HOTA primary؛ MOTA، IDF1، IDs، DetA، AssA، FPS، p50/p95 latency.

## 3. Vehicle ReID
| العائلة | الاستخدام | GPU/سرعة | تخصيص | قرار |
|---|---|---|---|---|
| CNN baseline | sanity check وablation | منخفضة/متوسطة | سهل | إلزامي قبل ViT |
| TransReID | transformer vehicle/object ReID | متوسطة/عالية | جيد مع pretraining | مرشح رئيسي |
| VehicleNet progressive | multi-source/domain robustness | training أعلى | يعتمد على component datasets | مرجع تعلم لا حزمة مغلقة |
| DINOv2 features | frozen/linear probe/embedding ablation | inference قد يكون مرتفعًا | يحتاج protocol خاص | تجريبي فقط |
| PVEN | غير معتمد في هذه المرحلة | غير محدد | سجل أصلي غير مثبت في المراجعة الحالية | لا يُدمج قبل التحقق |

**المقاييس:** mAP، Rank-1/5/10، cross-camera retrieval، calibration، abstention وfalse match rate عند threshold.

## 4. MTMC Association
### baseline قابل للتفسير
1. per-camera tracklets من ByteTrack/BoT-SORT.
2. crop embedding من CNN baseline ثم TransReID.
3. cosine distance مع temporal feasibility.
4. camera transition matrix وtravel-time prior.
5. Hungarian assignment ضمن نافذة محدودة.
6. candidate score مع threshold وunknown/abstain.

### alternatives / ablation
- appearance only.
- appearance + time.
- appearance + topology.
- appearance + time + topology.
- graph matching.
- GNN association فقط بعد توفر identities كافية وتقييم مستقل.

لا يُنشئ النظام history دائمًا أو identity graph غير محدود. association هو hypothesis مع confidence، purpose، TTL، access log.

## 5. License and model governance
- سجل `model_name`, `version`, `source_url`, `commit`, `weights_url`, `weights_license`, `dataset_license`, `commercial_status`.
- افصل ترخيص الكود عن ترخيص weights وعن ترخيص datasets.
- لا تضع weights كبيرة أو أسرارًا في Git.
- افحص dependencies وsecurity قبل deployment.

## 6. Resource benchmark protocol
قبل أي تدريب/استدلال:
- شغّل `python tools/environment_probe.py --output reports/environment_probe.json`.
- سجّل OS، Python، package lock، GPU name/VRAM/driver/CUDA، CPU/RAM/storage.
- جرّب FP32 وAMP عند دعم النموذج، مع فحص فرق الدقة.
- قس p50/p95 latency وthroughput بعد warmup، لا single sample.
- سجّل peak VRAM وbatch size وinput resolution.
- كرر 3 seeds للتجارب العلمية الحساسة، واستخدم confidence intervals عند الإمكان.

## 7. Recommended initial matrix
| Track | Baselines | Dataset candidate | Primary metrics |
|---|---|---|---|
| detection | YOLO-small/medium، RT-DETR | UA-DETRAC + local labeled split | mAP50-95، recall، latency |
| classification | detector head، crop classifier | UA-DETRAC + local taxonomy | macro-F1، balanced accuracy |
| S-C MOT | SORT، ByteTrack، BoT-SORT، OC-SORT | UA-DETRAC/AI City track | HOTA، IDF1، IDs |
| ReID | CNN، TransReID | VeRi-776، VehicleID، local split | mAP، Rank-1 |
| MTMC | appearance-only، fusion-Hungarian | CityFlow/CityFlowV2 + local | IDF1، HOTA، pairwise AP |
| adaptation | source-only، supervised FT، weak adaptation | source → local held-out time/camera | target mAP/HOTA/ReID + source regression |
| analytics | line/zone count، density estimator | local calibrated scenes | MAE/RMSE، directional F1 |

## 8. Acceptance thresholds
لا توضع عتبات جودة نهائية قبل pilot وقياس خط الأساس. عتبات البوابة الأولى تكون relative:
- لا regression أكبر من agreed tolerance على source holdout.
- تحسن target metric مع interval/seed evidence.
- latency وVRAM داخل budget مقاس فعليًا.
- false-match/abstention risk مقبول ومراجع بشريًا.
