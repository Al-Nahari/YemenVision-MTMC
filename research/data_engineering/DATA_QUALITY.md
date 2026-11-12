# Data Quality and Leakage Controls

## الفحوصات المنفذة

`data_engineering.quality` يوفر:

- incremental SHA-256 ووجود/قراءة الملفات.
- schema/bbox validation.
- duplicate `image_id` detection.
- missingness counts مع الحالات الأربع.
- class/camera/identity distributions.
- سجل أخطاء قابل للتصدير JSON.

فحوصات الصور/الفيديو كاملة (codec، frame decode، resolution، perceptual duplicates) تحتاج dependency للوسائط وبيانات فعلية؛ لم تُدّعَ على بيانات غير موجودة. يجب إضافة validator backend بعد تثبيت codec policy.

## التقسيم حسب المهمة

| المهمة | group الأساسي | سبب المنع |
|---|---|---|
| Detection | image أو clip حسب المصدر | يمنع frame duplicate، ويجب منع neighboring frames إذا كان الهدف تعميمًا زمنيًا |
| MOT | `video_id` | يمنع تسرب المشاهد/الحركة نفسها |
| ReID | `vehicle_id` | يمنع ظهور الهوية نفسها في train/test |
| MTMC | `vehicle_id`، أو fallback محافظ للفيديو/الصورة | يمنع تقييم association على tracklet مألوف |
| Forecasting | time-ordered windows | يمنع المستقبل في التدريب |

التقسيم الناتج deterministic عبر SHA-256 وseed. `leakage_report()` يراجع vehicle/video IDs عبر split؛ لا يغلق مخاطر camera/time دون metadata كافية.

## تقارير مطلوبة عند وجود data

1. file integrity: count، unreadable، zero-byte، hashes.
2. annotation validity: malformed، bbox خارج الحدود، negative/zero area.
3. duplicates: exact hash، image ID، perceptual duplicate عند توفر backend.
4. distribution: type، color، camera، identity، resolution، time، missingness.
5. leakage: identity/video/camera/time overlap، مع policy task.
6. QA: double-review agreement، adjudication rate، stratified error sample.

## سياسة الفشل

إذا كان `fail_on_corrupt_file` أو `fail_on_invalid_bbox` فعالًا، لا تنتقل البيانات إلى processed. لا تُصلح label بصمت؛ أنشئ correction log ونسخة annotation جديدة.
