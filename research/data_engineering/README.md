# Phase 02 — Data Engineering Foundation

هذه الحزمة تحول قرارات Phase 01 إلى بنية بيانات قابلة لإعادة البناء، دون تنزيل غير مصرح به أو ادعاء نتائج على datasets غير موجودة.

## المكونات

- `schema.py`: `UnifiedRecord`, `BoundingBox`, enums، provenance.
- `adapters/`: واجهة ومحولات مستقلة لكل dataset في الكتالوج؛ تتطلب release-normalized JSONL إلى أن يثبت layout الرسمي.
- `quality.py`: integrity/hash، validation، duplicate/missingness/distribution reports.
- `splits.py`: task-specific deterministic group splits وleakage report.
- `acquisition.py`: HTTPS-only resumable downloader gated by approval/license/hash.
- `cli/`: أوامر audit/download.
- `test_data_engineering.py`: اختبارات الوحدة باستخدام fixtures صغيرة.

## تشغيل

من مجلد `research` وبعد تهيئة Python environment:

```text
python -m unittest data_engineering.test_data_engineering -v
python -m data_engineering.cli.audit_dataset --dataset cityflow --source-root data/interim/fixture --release fixture --output data/reports/fixture_quality.json
```

تتطلب أوامر `python -m` تشغيلها من مجلد `research` أو ضبط `PYTHONPATH` عليه.

## البيانات الفعلية

لا يوجد تنزيل في هذه النسخة. راجع `DATA_ACQUISITION.md` و`data/manifests/download_manifest.json`. لا تستبدل placeholder إلا بعد مراجعة المصدر الرسمي، الترخيص، التفويض، الإصدار، وSHA-256.

## الجودة والخصوصية

Raw restricted، redacted derivatives، tracklets/features وaggregates طبقات منفصلة. لا يمثل `vehicle_id` هوية قانونية، ولا يحول cross-camera match الاحتمالي إلى سجل مفتوح. راجع `local_collection/` لإرشادات التصريح والوسم.
