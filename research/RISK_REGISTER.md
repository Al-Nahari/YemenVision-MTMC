# سجل المخاطر — YemenVision MTMC Phase 01

| ID | الخطر | الأثر | الاحتمال | الضابط | مالك القرار | الحالة |
|---|---|---|---|---|---|---|
| R01 | استخدام كاميرات/بيانات دون تصريح | قانوني/تشغيلي | متوسط | authorization + purpose + audit قبل ingestion | Data owner/Security | open |
| R02 | اعتبار match الاحتمالي هوية مؤكدة | ضرر قرار/خصوصية | متوسط | confidence، abstain، TTL، human review، لا سجل مفتوح | Product/Security | open |
| R03 | تخزين لوحات/وجوه خام | خصوصية/تسريب | متوسط | redaction افتراضي، raw restricted وTTL قصير | Security | open |
| R04 | ترخيص dataset غير مناسب تجاريًا | قانوني/مالي | مرتفع | license manifest وlegal sign-off لكل release | Legal/Data owner | open |
| R05 | نقل نتائج paper إلى اليمن | علمي | مرتفع | source labels، local independent test | Research | controlled |
| R06 | data leakage عبر frames أو vehicle IDs | تضخيم زائف للنتيجة | مرتفع | split by identity/camera/time، leakage tests | ML | open |
| R07 | domain shift | جودة منخفضة | مرتفع | target pilot، adaptation، subgroup metrics | CV/ML | open |
| R08 | topology/clock غير صحيح | false cross-camera links | متوسط | clock QA، versioned topology، abstain | Platform | open |
| R09 | detector failure تحت الغبار/الليل | miss/ID switches | مرتفع | low-light tests، quality flags، fallback sampling | CV | open |
| R10 | ضعف reproducibility | لا يمكن تدقيق النتائج | متوسط | lock files، seeds، manifests، checkpoints | MLOps | open |
| R11 | model/weights license mismatch | قانوني/توزيع | متوسط | artifact registry وlicense scan | MLOps/Legal | open |
| R12 | GPU/VRAM افتراض غير صحيح | فشل تشغيل/كلفة | متوسط | environment probe، AMP، profiling | DevOps | open |
| R13 | retention غير محدود | خصوصية/كلفة | متوسط | TTL، aggregate-first، deletion tests | Security | open |
| R14 | dashboard export يكشف مسارات | خصوصية/إساءة استخدام | متوسط | RBAC، aggregate/redacted views، audit | Backend | open |
| R15 | تلوث annotations/quality غير معروفة | نتيجة مضللة | متوسط | double review، sampling، label policy | Data | open |

## Risk acceptance rules
- لا يُغلق الخطر بكتابة وثيقة فقط؛ يلزم evidence/اختبار/موافقة.
- أي خطر privacy أو license غير محسوم يمنع production deployment.
- أي metric بلا split مستقل تصنف exploratory.
