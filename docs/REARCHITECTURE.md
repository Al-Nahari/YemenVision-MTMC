# YemenVision MTMC — خطة الهيكلة الاحترافية

## الهدف

تحويل النظام إلى منصة تحليل مروري قابلة للتوسع، مع الحفاظ على مسار الرفع الحالي:

```text
رفع فيديو → Job معالجة → كشف/تتبع/OCR → WebM قابل للتشغيل → أرشيف وسجلات
```

## الوضع المستهدف

### 1. طبقات النظام

- **Dashboard:** React/Vite، صفحات مقسمة lazy-loaded، API client موحد، حالات تحميل/خطأ واضحة.
- **API:** FastAPI مسؤول عن المصادقة، إدارة الكاميرات، إنشاء Jobs، الأرشيف، والتقارير.
- **Workers:** عمليات مستقلة لمعالجة الفيديو؛ لا تُنفّذ المعالجة الطويلة داخل طلب HTTP.
- **CV Pipeline:** Decoder → resize/stride → detector → tracker → OCR اختياري → encoder.
- **Storage:** PostgreSQL للأحداث والـ metadata، وS3/MinIO أو volume مخصص للوسائط.
- **Live Gateway:** RTSP يُحوّل في الخادم إلى WebRTC أو HLS؛ MJPEG يبقى fallback للتجارب المحلية فقط.

### 2. الأداء

- تحميل النموذج مرة واحدة مع lock وwarm-up عند بدء العامل.
- تحديد الدقة ومعدل الإطارات حسب profile: `cpu-safe`, `balanced`, `quality`.
- استخدام `torch.inference_mode()` وFP16 فقط عند توفر GPU مناسب.
- فصل OCR عن كل إطار: قراءة عند ظهور track جديد ومحاولات محدودة.
- عدم تنفيذ DB commit لكل كشف؛ تجميع الأحداث ثم commit دفعي.
- مراقبة `decode_fps`, `inference_ms`, `queue_depth`, `dropped_frames` و`ocr_ms`.

### 3. الدقة

- detector موثق في manifest مع رفض النماذج غير المطابقة.
- tracker ثابت لكل مصدر فيديو، مع منع تسرب حالة tracker بين الكاميرات.
- معايرة thresholds لكل فئة/كاميرا بدلاً من قيمة عامة فقط.
- حفظ confidence وmodel_version وframe_index مع كل قراءة.
- قياس الدقة على بيانات يمنية موسومة قبل إعلان أرقام إنتاجية؛ لا تُعتبر النتائج الحالية benchmark رسمي.

### 4. مراحل التنفيذ

1. **المرحلة الأولى:** تقسيم تحميل الواجهة، timeout موحد للـ API، وإعدادات Backend ثابتة.
2. **المرحلة الثانية (منفذة):** Job model (`queued/running/completed/failed`) مع worker محلي واحد وواجهة انتظار progress؛ يبقى المسار المتزامن متاحاً للتوافق.
3. **المرحلة الثالثة (منفذة جزئياً):** حفظ Jobs في جدول `inference_jobs` وتحديث progress أثناء قراءة الإطارات، مع fallback إلى السجل المحلي عند إعادة تشغيل API.
4. **المرحلة الرابعة (منفذة):** Queue Redis اختيارية، Worker مستقل، وتهيئة Docker للخدمة؛ الوضع المحلي يبقى fallback عند غياب Redis.
5. **المرحلة الخامسة (منفذة جزئياً):** Object Storage متوافق مع S3/MinIO كنسخة durable اختيارية، مع fallback محلي وتدفق media signed.
6. **مرحلة البث الإنتاجي (منفذة جزئياً):** جلسات HLS قصيرة العمر عبر FFmpeg، شبكة متعددة الكاميرات في الواجهة، وإيقاف جماعي؛ ملفات HLS مؤقتة تُحذف عند الإيقاف ولا تُسجل كفيديو أرشيفي.
7. **نتائج البث الحي:** MJPEG وHLS يشغلان كشفاً منخفض المعدل ويحفظان `DetectionEvent` فقط عند ربط الجلسة بكاميرا مسجلة؛ لا يُحفظ الفيديو الأصلي.
8. **تسريع الاستدلال:** يختار النظام تلقائياً CUDA على بطاقات NVIDIA، ثم Apple MPS، ثم CPU. يمكن فرض الاختيار عبر `YV_INFERENCE_DEVICE`، وتظهر النتيجة في `/api/v1/health`.

> ملاحظة تشغيل NVIDIA: وجود تعريف NVIDIA وحده لا يكفي؛ يجب تثبيت نسخة PyTorch تحتوي CUDA. في Windows استخدم Python 3.10–3.12 ثم `pip install -r backend/requirements-gpu-cu118.txt` بدلاً من نسخة CPU. بعد ذلك أعد تشغيل Backend وتحقق من `cuda_available: true` في health.
4. **الإنتاج:** FFmpeg/WebRTC للبث، Prometheus metrics، structured logs، health/readiness probes، وCI/CD.

## قرار مهم

لا ينبغي استبدال OpenCV أو YOLO عشوائياً. التحسين الصحيح هو قياس كل مرحلة أولاً، ثم اختيار FFmpeg/GStreamer أو ONNX Runtime/TensorRT بناءً على hardware الفعلي وبيانات الاختبار.
