"""Small local job runner used for long-running video inference.

It deliberately has no external dependency: one worker keeps CPU usage
predictable on weak machines. The interface is compatible with a future Redis
worker, so the HTTP API does not need to change when scaling out.
"""
from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4


@dataclass
class VideoJob:
    id: str
    status: str = 'queued'
    progress: int = 0
    camera_id: str = ''
    original_name: str = ''
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def public(self) -> dict[str, Any]:
        return asdict(self)


class LocalVideoJobRunner:
    def __init__(self, max_workers: int = 1):
        self._jobs: dict[str, VideoJob] = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix='yv-video')

    def submit(self, camera_id: str, original_name: str, task: Callable[[str], dict[str, Any]]) -> VideoJob:
        job = VideoJob(id=f'job_{uuid4().hex[:16]}', camera_id=camera_id, original_name=original_name)
        with self._lock:
            self._jobs[job.id] = job
        self._executor.submit(self._run, job.id, task)
        return job

    def get(self, job_id: str) -> VideoJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def _update(self, job: VideoJob, **changes: Any) -> None:
        with self._lock:
            for key, value in changes.items():
                setattr(job, key, value)
            job.updated_at = datetime.now(timezone.utc).isoformat()

    def _run(self, job_id: str, task: Callable[[str], dict[str, Any]]) -> None:
        job = self.get(job_id)
        if job is None:
            return
        self._update(job, status='running', progress=1)
        try:
            result = task(job_id)
            self._update(job, status='completed', progress=100, result=result)
        except Exception as exc:  # worker errors are reported through the job API
            self._update(job, status='failed', progress=100, error=str(exc))


video_jobs = LocalVideoJobRunner(max_workers=1)
