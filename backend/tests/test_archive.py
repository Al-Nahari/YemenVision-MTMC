import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault('DATABASE_URL', f"sqlite:///./test_archive_{uuid4().hex[:8]}.db")
os.environ.setdefault('API_KEYS_JSON', '{"admin":{"subject":"tester","roles":["admin","operator","analyst"]}}')
os.environ.setdefault('MEDIA_SIGNING_KEY', 'test-media-key')

from app.database import Base, SessionLocal, engine
from app.main import PROCESSED_VIDEO_DIR, app
from app.models import DetectionEvent


@pytest.fixture(scope='module', autouse=True)
def setup_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


def _headers() -> dict[str, str]:
    return {'x-api-key': 'admin'}


def test_camera_can_be_updated_and_deleted():
    with TestClient(app) as client:
        assert client.post('/api/v1/cameras', json={'id': 'edit_me'}, headers=_headers()).status_code == 201

        updated = client.put(
            '/api/v1/cameras/edit_me',
            json={'zone': 'شارع صنعاء', 'active': False, 'stream_url': 'rtsp://example.test/stream'},
            headers=_headers(),
        )
        assert updated.status_code == 200
        assert updated.json()['zone'] == 'شارع صنعاء'
        assert updated.json()['active'] is False

        listed = client.get('/api/v1/cameras', headers=_headers()).json()
        assert next(row for row in listed if row['id'] == 'edit_me')['zone'] == 'شارع صنعاء'

        deleted = client.delete('/api/v1/cameras/edit_me', headers=_headers())
        assert deleted.status_code == 200
        assert deleted.json()['status'] == 'deleted'
        remaining = client.get('/api/v1/cameras', headers=_headers()).json()
        assert all(row['id'] != 'edit_me' for row in remaining)


def test_legacy_video_is_registered_browsable_and_deletable():
    name = f'archive_{uuid4().hex[:8]}.webm'
    path = PROCESSED_VIDEO_DIR / name
    path.write_bytes(b'archive-probe')
    try:
        with TestClient(app) as client:
            rows = client.get('/api/v1/videos', headers=_headers()).json()
            match = next(row for row in rows if row['file_name'] == name)
            assert match['source'] == 'legacy'
            assert match['video_url'].startswith('/api/v1/media/')

            detail = client.get(f"/api/v1/videos/{match['id']}", headers=_headers())
            assert detail.status_code == 200
            assert detail.json()['file_name'] == name

            assert client.delete(f"/api/v1/videos/{match['id']}", headers=_headers()).status_code == 200
            assert not path.exists()
    finally:
        path.unlink(missing_ok=True)


def test_plates_endpoint_returns_stored_plate_numbers():
    db = SessionLocal()
    try:
        db.add(DetectionEvent(
            id=f'evt_plate_{uuid4().hex[:8]}', camera_id='plate_cam',
            occurred_at=datetime.now(timezone.utc), plate_text='YEM12345',
            payload={'event_type': 'vehicle_detection', 'video_id': 'clip',
                     'frame_index': 7, 'track_id': 3, 'plate_confidence': 0.91,
                     'plate_status': 'read'},
        ))
        db.commit()
    finally:
        db.close()

    with TestClient(app) as client:
        rows = client.get('/api/v1/plates?plate=YEM12', headers=_headers()).json()
        assert any(row['plate_text'] == 'YEM12345' for row in rows)
        assert next(row for row in rows if row['plate_text'] == 'YEM12345')['confidence'] == 0.91
