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

1. **المرحلة الحالية:** تقسيم تحميل الواجهة، timeout موحد للـ API، وإعدادات Backend ثابتة.
2. **المرحلة التالية:** Job model (`queued/running/completed/failed`) مع worker محلي وواجهة progress.
3. **مرحلة التوسع:** Redis queue + workers متعددة، PostgreSQL، وMinIO.
4. **الإنتاج:** FFmpeg/WebRTC للبث، Prometheus metrics، structured logs، health/readiness probes، وCI/CD.

## قرار مهم

لا ينبغي استبدال OpenCV أو YOLO عشوائياً. التحسين الصحيح هو قياس كل مرحلة أولاً، ثم اختيار FFmpeg/GStreamer أو ONNX Runtime/TensorRT بناءً على hardware الفعلي وبيانات الاختبار.
