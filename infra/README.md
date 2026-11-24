# Modal GPU runner

This is an optional remote GPU path. It does not change the default local
FastAPI/Redis workers.

## First run

```powershell
pip install modal
modal setup
modal run infra/modal_app.py
```

The Modal workspace must have billing/payment enabled for GPU functions.
Image building can succeed without billing, but starting a T4/L4 worker is
rejected until a payment method is configured.

Use another public video or a larger frame budget:

```powershell
modal run infra/modal_app.py --video-url "https://example/video.mp4" --max-frames 300
```

The worker downloads the video inside Modal, runs `detector_best.pt` on a T4,
and returns a JSON summary. API keys must remain in Modal secrets or the
backend; never expose them in the dashboard.
