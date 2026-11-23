"""Redis video worker.

Run in production with:
    python -m app.worker

The API remains usable without this process when ``YV_QUEUE_BACKEND=local``.
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.config import settings
from app.database import SessionLocal
from app.models import InferenceJob
from app.queue import dequeue_job
from app.schemas import InferenceVideoRequest
from app.services import process_uploaded_video

LOGGER = logging.getLogger('yemenvision.worker')
OUTPUT_DIR = Path(os.getenv('PROCESSED_VIDEO_DIR', 'processed-videos')).resolve()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_job(job_id: str) -> None:
    db = SessionLocal()
    output_path = OUTPUT_DIR / f'{uuid4().hex}.webm'
    try:
        row = db.get(InferenceJob, job_id)
        if row is None or not row.payload:
            return
        payload = row.payload
        source = Path(payload['video_path'])
        row.status, row.progress = 'running', 1
        row.updated_at = datetime.now(timezone.utc)
        db.commit()

        def report(frames: int, total: int | None) -> None:
            row.progress = max(1, min(99, round((frames / total) * 100) if total else 1))
            row.updated_at = datetime.now(timezone.utc)
            db.commit()

        request = InferenceVideoRequest(
            camera_id=row.camera_id,
            video_path=str(source),
            max_frames=payload.get('max_frames'),
            original_name=row.original_name,
        )
        result = process_uploaded_video(
            db, request, payload.get('actor', 'worker'), output_path,
            progress_callback=report,
        )
        row.status, row.progress, row.result = 'completed', 100, result.model_dump(mode='json')
        row.updated_at = datetime.now(timezone.utc)
        db.commit()
        source.unlink(missing_ok=True)
    except Exception as exc:
        LOGGER.exception('Video job %s failed', job_id)
        output_path.unlink(missing_ok=True)
        db.rollback()
        row = db.get(InferenceJob, job_id)
        if row:
            row.status, row.progress, row.error = 'failed', 100, str(exc)
            row.updated_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


def main() -> None:
    if settings.queue_backend != 'redis':
        raise SystemExit('Set YV_QUEUE_BACKEND=redis before starting the worker')
    LOGGER.info('YemenVision Redis worker started')
    while True:
        job_id = dequeue_job()
        if job_id:
            run_job(job_id)
        else:
            time.sleep(0.2)


if __name__ == '__main__':
    main()
