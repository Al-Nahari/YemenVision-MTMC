# Phase 0 audit and remediation log

Date: 2026-11-22  
Scope: `src/yemenvision`, `backend`, `dashboard`, `models`, `configs`, `tests`,
CI, Docker.

This document records what was checked, what was fixed in the working tree, and
what is still blocked. It deliberately does not turn unmeasured metrics into
claims.

## Executive status

- The core package test suite passes (`19 passed`).
- The legacy backend test suite passes (`9 passed`).
- The Angular dashboard builds successfully (`400.27 kB` initial bundle).
- The secret scan finds no credential patterns in the working tree.
- **ReID is not usable**: the local `models/reid_best.pt` is truncated and is
  revoked by both manifests.
- **Detector validation is blocked in this shell** because OpenCV (`cv2`) is not
  installed. The file hash and ZIP structure are valid.
- Detection, MOT, ReID, and MTMC quality metrics remain `NOT_EVALUATED`.

## P0 findings and disposition

| # | Finding | Disposition |
|---|---|---|
| 1 | `reid_best.pt` truncated | Documented and revoked in `models/manifest.json` and `models/production_manifest.json`. Registry now detects truncated archives before `torch.load`. Re-export still required. |
| 2 | Conflicting ReID hashes | `manifest.json` now uses the promoted hash (`956b55a3...`) and records the observed local hash separately. Both manifests agree on the promoted artifact. |
| 3 | Backend produced simulated tracks/embeddings | Simulated `run_video_inference` path removed; the old endpoint returns `410`. Random embedding fallback removed. Upload inference uses the real detector or fails closed. |
| 4 | Silent COCO fallback | `ModelManager` now loads only a registry-selected detector and rejects a non-21-class label space. No `yolo11n.pt` fallback remains in the backend service. |
| 5 | Registry bypass | `ModelManager` uses `ModelRegistry.select("detector")` and the backend exposes `GET /api/v1/models`. |
| 6 | No plate blur on upload | Uploaded frames are redacted before annotation/write. With no detection the whole frame is blurred (fail-closed). |
| 7 | Processed videos exposed via `StaticFiles` | Static mount removed. Media is served through HMAC-signed, expiring `/api/v1/media/{name}` URLs. |
| 8 | New API was a stub | Still scaffolded. It reports `NOT_EVALUATED` rather than fabricating a result; a durable worker is a Phase 1 item. |
| 9 | CI referenced deleted paths | Workflow rewritten: core lint/tests, legacy backend tests, dashboard build. |
| 10 | Hard-coded compose secrets | Root and backend compose files now require secrets from the environment. |

## P1 findings touched in this pass

- Tracking defaults now match `configs/default.yaml` (`high=0.55`, `new=0.55`).
- `new_track_thresh` is validated by `Settings.validate()`.
- `run_mtmc` accepts `appearance_weight` and the CLI passes the configured value
  instead of silently using the library default.
- Privacy policy in the backend is configurable: blur is opt-in, and plate
  numbers are read by throttled CPU OCR from the lower vehicle region and stored
  in `detection_events.plate_text`. A dedicated plate detector would still
  improve recall over the crop heuristic.
- CI now fails on lint errors, syntax errors, secret patterns, core tests, backend
  tests, or a broken dashboard build.

## Remaining blockers (not fixed here)

1. Re-export or restore the promoted ReID checkpoint and remove its revocation.
2. Install a working `opencv-python-headless` runtime in the execution
   environment and re-run `yv check-models`.
3. Implement durable jobs (Redis/RQ or equivalent), Postgres job state, and
   Alembic migrations for the backend.
4. Replace the crop-based OCR heuristic with a dedicated plate detector and add
   a recognition-quality regression test with real frames.
5. Make audit logs append-only/hash-chained and add the retention job.
6. Add MOT/MTMC/ReID evaluation datasets and publish measured reports.
7. Split the Angular page component and remove API keys from `localStorage`.

## Verification commands

```powershell
python -m pytest -q
$env:PYTHONPATH = "backend"; python -m pytest backend/tests -q
python -m ruff check src tests backend tools
python tools/secret_scan.py .
$env:YV_MODELS_DIR = "models"; yv check-models --json
cd dashboard; npm run build
```

See `docs/BASELINE.md` for the exact observed outputs.
