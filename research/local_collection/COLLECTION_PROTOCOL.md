# بروتوكول جمع محلي مصرح به

## قبل الالتقاط

- اعتماد authorization من مالك الكاميرا والجهة القانونية/الأمنية.
- تحديد الغرض: traffic analytics أو تقييم نموذج، وليس إنشاء سجل تتبع مفتوح.
- تحديد retention وroles وaudit ونسخة سياسة الخصوصية.
- جرد الكاميرات والتوقيت وFOV والتزامن والمعايرة.
- اختبار redaction قبل استقبال الإنتاج؛ فشل redaction يعني fail-closed للعرض والتصدير.

## أثناء الالتقاط

- استخدام معرفات كاميرات pseudonymous.
- تسجيل UTC timestamp، frame index، release، وأحداث الانقطاع/الساعة.
- لا تضع أسرارًا أو روابط وصول خاصة في manifests أو logs.
- افصل raw restricted عن redacted derivatives.

## بعد الالتقاط

- تحقق من سلامة الملفات وSHA-256 وcodec/frame count.
- نفذ redaction، ثم راجع عينة يدويًا.
- أنشئ data card وannotation manifest وquality report.
- احذف الملفات التي انتهت مدة احتفاظها، وسجل deletion event دون نسخ المحتوى.
- لا تُستخدم البيانات في التدريب قبل إغلاق بوابة الترخيص والخصوصية.
