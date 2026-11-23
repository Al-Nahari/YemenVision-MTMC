# Baseline report

Date: 2026-11-22  
Purpose: record what was actually executed and measured in this checkout. Do not
treat the numbers below as model-quality claims.

## Environment observed

| Item | Value |
|---|---|
| OS | Windows 10/11 (local development shell) |
| Python | 3.14.7 |
| Node | 26.13.0 (local); CI uses Node 22 |
| npm | 11.20.0 |
| CUDA / GPU | not probed |
| OpenCV | not installed in this shell (`import cv2` fails) |
| Model weights | present locally but gitignored |

CI uses Python 3.11 on Ubuntu for the core and backend jobs, and Node 22 for the
dashboard.

## Measurements

### Core package

```text
python -m pytest -q
19 passed
```

### Legacy backend

```text
$env:PYTHONPATH = "backend"
python -m pytest backend/tests -q
9 passed, 1 warning
```

The warning is a Starlette deprecation notice about `httpx` and
`TestClient`; it is not a test failure.

### Lint and syntax

```text
python -m ruff check src tests backend tools
All checks passed!

python -m compileall -q src tests backend tools
(no output; exit 0)
```

### Secret scan

```text
python tools/secret_scan.py .
secret scan: no credential patterns found
```

### Dashboard

```text
cd dashboard
npm run build
Initial total: 400.27 kB (estimated transfer 99.34 kB)
Application bundle generation complete.
```

### Model registry

`yv check-models --json` currently reports `FAIL`:

- `detector_best.pt`: SHA-256 matches the manifest
  (`8166b818...`), but checkpoint validation fails because `cv2` is missing.
- `reid_best.pt`: revoked; local SHA-256 (`3cd6b60e...`) does not match the
  promoted hash (`956b55a3...`); the local file is not a valid ZIP archive.
- `vehicle_attributes.pt`: valid auxiliary artifact.

This is the expected truthful result for this environment. A model is not
"available" just because a file exists.

## Not evaluated

The following are explicitly `NOT_EVALUATED` because the required data or
runtime is absent:

| Area | Metric | Why |
|---|---|---|
| Detection | mAP50, mAP50-95, per-class AP | no labeled validation split and no working OpenCV runtime |
| Tracking | HOTA, IDF1, MOTA, ID switches | no MOT ground truth |
| ReID | mAP, Rank-1/5/10 | checkpoint revoked; no VeRi/local evaluation split |
| MTMC | Link precision/recall, IDF1, false-link rate | no synchronized multi-camera ground truth or calibrated topology |
| Performance | p95 upload-to-result, throughput | no representative videos/GPU run |
| Privacy | false-negative plate exposure rate | only a heuristic blur is wired; no plate-detector evaluation |

## Reproduction notes

- The backend tests set `DATABASE_URL` and `API_KEYS_JSON` themselves and use
  SQLite; they do not require Postgres.
- Upload tests intentionally accept `422` or `503` for unreadable input because
  both are truthful failures: the file may be undecodable, or the model runtime
  may be unavailable.
- `models/` is mounted read-only in compose; tests never download weights.
