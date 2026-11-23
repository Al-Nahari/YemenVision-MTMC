"""Optional S3/MinIO artifact storage.

Local disk remains the primary fallback. When configured, every completed
artifact is copied to object storage for durable retention and future HLS/CDN
delivery without changing the API contract.
"""
from __future__ import annotations

from pathlib import Path

from app.config import settings


def enabled() -> bool:
    return bool(
        settings.object_storage_endpoint
        and settings.object_storage_access_key
        and settings.object_storage_secret_key
    )


def put_file(path: Path, key: str) -> bool:
    if not enabled():
        return False
    try:
        import boto3
        client = boto3.client(
            's3', endpoint_url=settings.object_storage_endpoint,
            aws_access_key_id=settings.object_storage_access_key,
            aws_secret_access_key=settings.object_storage_secret_key,
            region_name=settings.object_storage_region,
        )
        client.upload_file(str(path), settings.object_storage_bucket, key, ExtraArgs={'ContentType': 'video/webm'})
        return True
    except Exception:
        return False


def stream_file(key: str):
    """Return a boto3 streaming body, or None when storage is unavailable."""
    if not enabled():
        return None
    import boto3
    client = boto3.client(
        's3', endpoint_url=settings.object_storage_endpoint,
        aws_access_key_id=settings.object_storage_access_key,
        aws_secret_access_key=settings.object_storage_secret_key,
        region_name=settings.object_storage_region,
    )
    return client.get_object(Bucket=settings.object_storage_bucket, Key=key)['Body']
