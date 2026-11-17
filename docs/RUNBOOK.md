# Runbook

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
$env:YV_MODELS_DIR = "C:\path\to\models"
yv check-models
```

Install optional runtime groups only when required: `.[detection]`, `.[reid]`, `.[api]`, and `.[evaluation]`. The current workstation has no Torch/Ultralytics/OpenCV/ffmpeg and no model artifacts, so model-dependent commands are expected to report an explicit missing dependency or `NOT_EVALUATED` state.

Do not place API keys in notebooks, code, manifests, or Docker compose files. Use environment variables or a managed secret store. Rotate any key previously exposed in the untracked Colab notebooks before use.
