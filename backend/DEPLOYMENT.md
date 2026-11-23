# Local deployment

1. Copy `backend/.env.example` to `backend/.env` and set `API_KEYS_JSON`,
   `MEDIA_SIGNING_KEY`, and any non-default model/privacy values.
2. Create an isolated environment and install `pip install -r requirements.txt`
   plus the project package (`pip install -e ..`). If the environment already
   uses `opencv-python-headless`, install OCR without pulling the conflicting
   GUI build: `pip install --no-deps rapidocr-onnxruntime` (its remaining
   dependencies `onnxruntime`, `shapely`, and `pyclipper` are already in the
   requirements chain). OCR is optional; the API still works without it.
3. Start locally with `uvicorn app.main:app --reload`; OpenAPI is at
   `/api/v1/docs`.
4. Run `pytest`. For a production-like stack, export
   `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `API_KEYS_JSON`, and
   `MEDIA_SIGNING_KEY`, then run `docker compose up --build` from the
   repository root (the root compose file builds the shared core and mounts
   `models/` read-only).

Do not use SQLite, static API keys, the example secrets, or auto-created schema as production controls. Apply reviewed SQL migrations, OIDC/MFA, TLS, managed secrets, backups, observability, and retention deletion jobs first.
