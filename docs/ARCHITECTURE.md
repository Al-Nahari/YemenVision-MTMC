# YemenVision-MTMC architecture

The installable package under `src/yemenvision/` is the production boundary. It is dependency-injected and does not contain a training loop or a fabricated fallback.

- `registry`: read-only discovery, SHA-256 and checkpoint-contract validation.
- `detection`: YOLO adapter with the fixed 21-class contract.
- `tracking`: camera-local tracklet records; local IDs are never global identities.
- `reid`: ResNet50 feature map + adaptive pooling + BNNeck, then L2 normalization and optional flip-TTA.
- `association`: topology/time constrained candidate links and one-to-one assignment.
- `pipeline`: streaming video processing; missing codecs, models, or input files fail explicitly.
- `privacy`: explicit plate-box blur utility. OCR is not implemented and is disabled.
- `io`: JSONL and auditable run manifests.
- `eval`: typed `PASS`, `FAIL`, and `NOT_EVALUATED` result status.

The existing `backend/` remains a legacy API surface during migration. It must not be treated as evidence of measured ML accuracy.
