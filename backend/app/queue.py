"""Optional Redis queue with a local-install friendly fallback."""
from __future__ import annotations

from app.config import settings


def enqueue_job(job_id: str) -> bool:
    """Push a job id to Redis; return False when Redis is unavailable."""
    if settings.queue_backend != 'redis':
        return False
    try:
        import redis
        client = redis.Redis.from_url(settings.redis_url, decode_responses=True, socket_timeout=3)
        client.rpush(settings.redis_queue_name, job_id)
        return True
    except Exception:
        return False


def dequeue_job(timeout: int = 5) -> str | None:
    import redis
    client = redis.Redis.from_url(settings.redis_url, decode_responses=True, socket_timeout=timeout + 1)
    item = client.blpop(settings.redis_queue_name, timeout=timeout)
    return item[1] if item else None
