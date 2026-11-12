# Split manifests

هذه المساحة مخصصة لملفات تقسيم قابلة لإعادة البناء، ولا تحتوي على بيانات فعلية في هذا الإصدار.

- `reid`: group by `vehicle_id`.
- `mot` and `forecasting`: group by `video_id`.
- `mtmc`: group by `vehicle_id` when available; otherwise use a conservative video/image group.
- `detection`: image-level groups are acceptable only when neighboring frames are not mixed.

كل manifest يجب أن يسجل `dataset_source`, `release`, `seed`, `task`, `data_hash`, ونسخة الكود. أي سجل لا يملك هوية أو فيديو يجب أن يبقى `unassigned` أو يدخل تجربة موسومة بوضوح بأنها exploratory.
