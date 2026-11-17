from __future__ import annotations

import os
import secrets
import shutil
import tempfile
import threading
import uuid
from pathlib import Path
from typing import Any


def create_app() -> Any:
    try:
        from fastapi import BackgroundTasks, Depends, FastAPI, File, Header, HTTPException, UploadFile
    except ImportError as exc:
        raise RuntimeError("API requires fastapi and python-multipart; install yemenvision-mtmc[api]") from exc

    app = FastAPI(title="YemenVision-MTMC", version="0.1.0")
    jobs: dict[str, dict[str, Any]] = {}
    lock = threading.Lock()
    max_bytes = int(os.getenv("YV_MAX_UPLOAD_BYTES", str(512 * 1024 * 1024)))
    api_key = os.getenv("YV_API_KEY")

    def auth(authorization: str | None = Header(default=None)) -> None:
        if api_key and authorization != f"Bearer {api_key}":
            raise HTTPException(401, "invalid API key")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "yemenvision"}

    @app.get("/models")
    def models(_: None = Depends(auth)) -> dict[str, Any]:
        from yemenvision.registry import ModelRegistry
        return {"models": [record.as_dict() for record in ModelRegistry().discover()]}

    @app.post("/jobs", status_code=202)
    async def create_job(background: BackgroundTasks, video: UploadFile = File(...), _: None = Depends(auth)) -> dict[str, str]:
        suffix = Path(video.filename or "input.mp4").suffix.lower()
        if suffix not in {".mp4", ".avi", ".mkv", ".mov"}:
            raise HTTPException(415, "unsupported video extension")
        job_id = uuid.uuid4().hex
        root = Path(tempfile.mkdtemp(prefix=f"yv_{job_id}_"))
        source = root / f"input{suffix}"
        size = 0
        with source.open("wb") as handle:
            while chunk := await video.read(1024 * 1024):
                size += len(chunk)
                if size > max_bytes:
                    shutil.rmtree(root, ignore_errors=True)
                    raise HTTPException(413, "upload exceeds configured size limit")
                handle.write(chunk)
        with lock:
            jobs[job_id] = {"id": job_id, "status": "QUEUED", "root": str(root), "results": None}
        background.add_task(_mark_unavailable, jobs, lock, job_id)
        return {"id": job_id, "status": "QUEUED"}

    @app.get("/jobs/{job_id}")
    def job(job_id: str, _: None = Depends(auth)) -> dict[str, Any]:
        with lock:
            item = jobs.get(job_id)
        if not item:
            raise HTTPException(404, "job not found")
        return {key: value for key, value in item.items() if key != "root"}

    @app.get("/jobs/{job_id}/results")
    def results(job_id: str, _: None = Depends(auth)) -> Any:
        with lock:
            item = jobs.get(job_id)
        if not item:
            raise HTTPException(404, "job not found")
        if item["status"] != "COMPLETED":
            raise HTTPException(409, "job has no completed results")
        return item["results"]

    return app


def _mark_unavailable(jobs: dict[str, dict[str, Any]], lock: threading.Lock, job_id: str) -> None:
    with lock:
        jobs[job_id]["status"] = "NOT_EVALUATED"
        jobs[job_id]["reason"] = "API queue is scaffolded; configure a worker with authorized models before processing uploads"
