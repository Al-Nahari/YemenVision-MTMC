# YemenVision-MTMC

Auditable vehicle detection, camera-local tracking, vehicle ReID, and topology-constrained multi-camera association.

## Truthful status

The repository contains research modules and an installable production foundation. No model weights, video, synchronized multi-camera ground truth, or VeRi evaluation data are present in this workspace. Therefore model metrics, MOT, and official MTMC results are `NOT_EVALUATED`. The original numeric references are not claims about this checkout.

## Install

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Optional runtime dependencies: `pip install -e ".[detection,reid,api,evaluation]"`.

## Model checks

```powershell
$env:YV_MODELS_DIR = "C:\path\to\models"
yv check-models
```

Models are read-only and never downloaded or overwritten. See `models/README.md` and `docs/MODELS.md`.

## Existing research/backend

`research/` contains prior detector, tracker, ReID, association, and traffic experiments. `backend/` is a legacy FastAPI modular monolith and is not a substitute for the new dependency-injected inference package. The Colab notebooks are research artifacts only and are not production entry points.

## Privacy and limitations

Plate blur is enabled by policy for saved imagery; OCR is not implemented. ReID was trained/evaluated on VeRi-776 and transfer to Yemeni traffic is unproven. Cross-camera identity association is probabilistic and must abstain without calibrated topology/time data and ground truth.
