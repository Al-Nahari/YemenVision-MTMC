# Local deployment

1. `cd backend`; copy `.env.example` to `.env` and replace every `change-me` value.
2. Create an isolated environment and install `pip install -r requirements.txt`.
3. Start locally with `uvicorn app.main:app --reload`; OpenAPI is at `/api/v1/docs`.
4. Run `pytest`. For a production-like stack, set PostgreSQL credentials in `.env` and run `docker compose up --build`.

Do not use SQLite, static API keys, the example secrets, or auto-created schema as production controls. Apply reviewed SQL migrations, OIDC/MFA, TLS, managed secrets, backups, observability, and retention deletion jobs first.
