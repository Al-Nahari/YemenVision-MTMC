# YemenVision-MTMC

Auditable vehicle detection, camera-local tracking, vehicle ReID, and
topology-constrained multi-camera association.

## Truthful status

The repository contains an installable CV core, a legacy FastAPI backend, and an
Angular dashboard. Model weights are **not tracked by git**; some files may be
present locally.

- Detection, MOT, ReID, and official MTMC metrics are `NOT_EVALUATED`. No
  synchronized multi-camera ground truth or VeRi evaluation split is included.
- `models/reid_best.pt` is truncated in this checkout and is revoked by both
  model manifests. Do not use it for ReID or MTMC results.
- `models/detector_best.pt` matches its manifest SHA-256, but validating it
  requires a working OpenCV runtime (`cv2`).
- Plate numbers are read with throttled CPU OCR and stored in the event logs;
  video blur is now opt-in for deployments that need redacted output.
- `docs/PERFORMANCE_PLAN.md` documents the CPU budget and scaling plan.

See `docs/AUDIT.md`, `docs/BASELINE.md`, `docs/MODELS.md`, and
`docs/PERFORMANCE_PLAN.md` for evidence and open blockers.

## Install

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Optional runtime dependencies: `pip install -e ".[detection,reid,api,evaluation]"`.
For CPU plate OCR in the backend, run
`pip install --no-deps -r backend/requirements-ocr.txt` after installing the
backend requirements.

## Model checks

```powershell
$env:YV_MODELS_DIR = "C:\path\to\models"
yv check-models
yv check-models --trusted-models-only
```

Models are read-only and never downloaded or overwritten. The registry verifies
manifest hashes, revocations, the 21-class contract, and truncated archives
before a component loads a checkpoint. See `docs/MODELS.md`.

## Run the CV core

```powershell
yv run path\to\video.mp4 --camera-id cam01 --trusted-models-only
yv mtmc outputs\runs\cam01 outputs\runs\cam02 --output-dir outputs\mtmc --topology configs\cameras.example.yaml
```

`yv run` fails closed if a verified detector is unavailable. `yv mtmc` abstains
when topology or identity-linked ground truth is missing.

## Legacy backend and dashboard

The backend is a modular-monolith API around the same core; it is not a
replacement for the dependency-injected package. The dashboard is a React + Vite
single-page application.

```powershell
$env:PYTHONPATH = "backend"
uvicorn app.main:app --reload
```

OpenAPI is at `/api/v1/docs`. Uploaded videos are processed synchronously with
the verified detector, redacted before saving, and served through short-lived
HMAC-signed URLs (`/api/v1/media/...`). The previous server-path inference
endpoint is disabled and returns `410`.

The dashboard lives in `dashboard/`:

```powershell
cd dashboard
npm ci
npm run build
```

## Tests and CI

```powershell
python -m pytest -q
$env:PYTHONPATH = "backend"; python -m pytest backend/tests -q
python -m ruff check src tests backend tools
python tools/secret_scan.py .
```

CI runs the core tests, legacy backend tests, lint/compile checks, secret scan,
and the Angular production build.

## Privacy and limitations

Plate blur is enabled by policy for saved imagery; OCR is not implemented. The
backend redacts the lower region of each detected vehicle and fully blurs frames
where no vehicle was detected. ReID was trained/evaluated on VeRi-776 and
transfer to Yemeni traffic is unproven. Cross-camera identity association is
probabilistic and must abstain without calibrated topology/time data and ground
truth.
