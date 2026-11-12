# تقرير Data Readiness — Phase 02

**التاريخ:** 2026-11-12  
**الحالة:** `CONDITIONAL / NOT_READY_FOR_TRAINING`

## ما تم تنفيذه

- عقد schema موحد في `data_engineering/schema.py` مع bbox/provenance وmissingness صريح.
- registry ومحولات مستقلة بالأسماء: CityFlow، CityFlowV2، AI City، VeRi-776، VehicleID، VehicleNet، UA-DETRAC.
- quality audit للـJSONL، التكرار، missingness، التوزيعات، وأخطاء السجل.
- split strategy حسب المهمة مع فحص تسرب vehicle/video.
- downloader متقطع ومحدود بـHTTPS، موافقة، license verification وSHA-256.
- DVC scaffold وmanifest/provenance وconfig.
- بروتوكول جمع محلي وإرشادات annotation/redaction.
- دفاتر تحليل قابلة لإعادة البناء، مع fixtures فقط لا تمثل datasets فعلية.

## ما تم اختباره

| الاختبار | النتيجة |
|---|---|
| schema defaults وbbox errors | سيتم تسجيل النتيجة بعد التشغيل الفعلي |
| JSONL adapter/provenance/duplicate report | سيتم تسجيل النتيجة بعد التشغيل الفعلي |
| ReID identity split leakage | سيتم تسجيل النتيجة بعد التشغيل الفعلي |
| unverified download rejection | سيتم تسجيل النتيجة بعد التشغيل الفعلي |
| Phase 01 regression tests | سيتم تسجيل النتيجة بعد التشغيل الفعلي |

## ما لم يُختبر

- أي dataset عامة فعلية؛ لم يحدث تنزيل.
- decoding للفيديو، codec، corruption على ملفات كبيرة.
- perceptual duplicate detection.
- annotation agreement على annotators حقيقيين.
- DVC remote/rebuild وMLflow backend.
- GPU أو throughput.

## أسباب عدم الجاهزية للتدريب

1. لا توجد release manifests موثقة مع hashes وحقوق استخدام مؤكدة.
2. لا توجد بيانات يمنية مصرح بها أو local annotation release.
3. لا توجد camera/time/identity split manifests فعلية.
4. adapters الحالية تحفظ عقدًا ثابتًا لكنها تتطلب release-normalized annotations؛ لم تُثبت على layouts الأصلية.
5. لا توجد تقارير جودة على صور/فيديو فعلي.

## بوابة الانتقال

يمكن الانتقال إلى ingestion validation بعد اعتماد مالك البيانات/القانون للـreleases، ثم تشغيل adapters على نسخة رسمية، إصدار data cards وquality reports، وإغلاق تسرب معروف. لا يبدأ التدريب قبل أن تصبح الحالة `READY_FOR_TRAINING` بتوقيع Data Owner وResearch وSecurity.
