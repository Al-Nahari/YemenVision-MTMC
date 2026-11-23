import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault('DATABASE_URL', f"sqlite:///./test_{uuid4().hex[:8]}.db")
os.environ.setdefault('API_KEYS_JSON', '{"admin":{"subject":"tester","roles":["admin"]}}')
os.environ.setdefault('MEDIA_SIGNING_KEY', 'test-media-key')

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.database import Base, engine
from app.main import PROCESSED_VIDEO_DIR, app
from app.media import media_url
from app.services import json_safe


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


def _headers() -> dict[str, str]:
    return {'x-api-key': 'admin'}


def test_server_path_inference_is_disabled():
    with TestClient(app) as client:
        response = client.post(
            '/api/v1/inference/video',
            json={'camera_id': 'test_cam_01', 'video_path': 'sample_stream.mp4', 'max_frames': 15},
            headers=_headers(),
        )
        assert response.status_code == 410
        assert 'upload' in response.json()['detail'].lower()


def test_upload_rejects_non_video_content_type():
    with TestClient(app) as client:
        response = client.post(
            '/api/v1/inference/upload?camera_id=test_cam_01',
            content=b'not a video',
            headers={**_headers(), 'content-type': 'text/plain', 'x-file-name': 'sample.mp4'},
        )
        assert response.status_code == 415


def test_upload_rejects_invalid_frame_count():
    with TestClient(app) as client:
        response = client.post(
            '/api/v1/inference/upload?camera_id=test_cam_01&max_frames=0',
            content=b'not a real video',
            headers={
                **_headers(),
                'content-type': 'video/mp4',
                'x-file-name': 'sample.mp4',
            },
        )
        assert response.status_code == 422


def test_unreadable_upload_fails_closed():
    with TestClient(app) as client:
        response = client.post(
            '/api/v1/inference/upload?camera_id=test_cam_01',
            content=b'not a real video',
            headers={
                **_headers(),
                'content-type': 'video/mp4',
                'x-file-name': 'sample.mp4',
            },
        )
        # 422 when OpenCV is available but cannot decode; 503 when the runtime
        # or model is unavailable. Both are truthful failures, never fake data.
        assert response.status_code in (422, 503)
        assert 'simulated' not in response.text.lower()


def test_media_requires_a_valid_signature():
    name = 'probe.mp4'
    path = PROCESSED_VIDEO_DIR / name
    path.write_bytes(b'probe')
    try:
        with TestClient(app) as client:
            invalid = client.get(f'/api/v1/media/{name}?exp=9999999999&sig=bad')
            assert invalid.status_code == 403

            signed = client.get(media_url(name))
            assert signed.status_code == 200
            assert signed.content == b'probe'
    finally:
        path.unlink(missing_ok=True)


def test_tracklet_payload_timestamps_are_json_serializable():
    timestamp = datetime(2026, 11, 23, 12, 30, tzinfo=timezone.utc)
    payload = json_safe({'start': timestamp, 'box': [1.0, 2.0], 'nested': {'end': timestamp}})
    assert payload['start'] == timestamp.isoformat()
    assert payload['nested']['end'] == timestamp.isoformat()


def test_media_serves_webm_with_browser_mime_type():
    name = 'probe.webm'
    path = PROCESSED_VIDEO_DIR / name
    path.write_bytes(b'probe')
    try:
        with TestClient(app) as client:
            response = client.get(media_url(name))
            assert response.status_code == 200
            assert response.headers['content-type'].startswith('video/webm')
    finally:
        path.unlink(missing_ok=True)
