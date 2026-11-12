# Unified Data Schema — YemenVision MTMC Phase 02

## الهدف

يوحّد هذا العقد سجلات الصور والإطارات والمسارات وReID دون إخفاء الحقول غير المتاحة في المصدر. كل سجل يحتفظ بـ`dataset_source` و`source_release` و`source_file`، وعند توفره `source_sha256` و`source_annotation_id`.

## الحقول الأساسية

| الحقل | النوع | مطلوب | المعنى |
|---|---|---:|---|
| `image_id` | string | نعم | معرف فريد داخل release، وليس اسمًا عشوائيًا عند وجود collision |
| `video_id` | string/null | لا | معرف الفيديو المصدر |
| `camera_id` | string/null | لا | معرف الكاميرا المصدر أو pseudonymous local ID |
| `timestamp` | RFC3339 string/null | لا | وقت الالتقاط، لا يُنشأ إذا لم يقدمه المصدر |
| `frame_index` | integer/null | لا | رقم الإطار غير السالب |
| `vehicle_id` | string/null | لا | هوية source-scoped؛ لا تمثل شخصًا أو مالكًا |
| `track_id` | string/null | لا | مسار محلي داخل camera/video/session |
| `bbox` | object/null | لا | `x_min,y_min,x_max,y_max` في pixel space |
| `vehicle_type` | string/null | لا | taxonomy المصدر بعد label mapping |
| `vehicle_color` | string/null | لا | لون مرئي فقط، أو null |
| `vehicle_attributes` | object | نعم | attributes مع confidence وunknown عند الحاجة |
| `dataset_source` | string | نعم | اسم المصدر المعياري |
| `split` | enum | نعم | train/validation/test/unassigned، لكل مهمة على حدة |
| `annotation_status` | object | نعم | حالة كل حقل: annotated/unknown/not_annotated/not_applicable |

## Provenance fields

`source_file`, `source_release`, `source_annotation_id`, و`source_sha256` ليست بديلًا عن الحقول الأساسية؛ وجودها مطلوب في البيانات المعالجة عندما يمكن حسابها. لا تُخلط namespaces للهويات بين datasets.

## Missingness semantics

- `annotated`: القيمة موجودة ومراجعة وفق مصدرها.
- `unknown`: المصدر أو المراجع يصرح أن القيمة غير معروفة/غير قابلة للتحديد.
- `not_annotated`: المصدر لم يوفر الحقل.
- `not_applicable`: الحقل لا ينطبق على هذا السجل/المهمة.

لا تستخدم سلسلة `unknown` وحدها لإثبات أن المصدر قام بالوسم. استخدم `annotation_status`.

## Adapter contract

كل adapter ينفذ `iter_records() -> Iterator[UnifiedRecord]`، ويجب أن:

1. يقرأ release محددًا لا mirror غير مثبت.
2. يحافظ على أسماء المصدر في provenance.
3. يطبق label mapping versioned.
4. لا يخترع timestamp/camera/identity غير موجودة.
5. يرفض JSON/annotations غير الصالحة بدل إسقاط السجلات بصمت.
6. ينتج تقريرًا بعدد السجلات، الأخطاء، التكرارات، missingness، والكاميرات/الهويات.

## مثال JSONL

```json
{"image_id":"cam01_000001.jpg","video_id":"v01","camera_id":"cam01","frame_index":1,"bbox":{"x_min":12,"y_min":20,"x_max":180,"y_max":140},"vehicle_id":null,"dataset_source":"fixture","split":"unassigned","annotation_status":{"vehicle_id":"not_annotated","bbox":"annotated"},"vehicle_attributes":{}}
```

## حدود السلامة

`vehicle_id` وembeddings ليست هوية قانونية. لا يحول هذا schema أي match احتمالي إلى حقيقة. تعرض الواجهات نسخًا redacted، وتُقيد البيانات الخام والسمات الحساسة بالتصريح وTTL والتدقيق.
