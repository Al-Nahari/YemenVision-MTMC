import os
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

os.environ['DATABASE_URL'] = f"sqlite:///./test_{uuid4().hex[:8]}.db"
os.environ['API_KEYS_JSON'] = '{"admin":{"subject":"tester","roles":["admin"]}}'

from app.main import app
from app.database import Base, engine

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

def test_inference_video_endpoint():
    with TestClient(app) as c:
        headers = {'x-api-key': 'admin'}
        # Request inference on sample video path
        req_data = {
            "camera_id": "test_cam_01",
            "video_path": "sample_stream.mp4",
            "conf_threshold": 0.3,
            "iou_threshold": 0.4,
            "max_frames": 15
        }
        res = c.post('/api/v1/inference/video', json=req_data, headers=headers)
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["status"] == "completed"
        assert data["camera_id"] == "test_cam_01"
        assert data["frames_processed"] == 15
        assert data["tracklets_count"] > 0
        assert data["events_count"] > 0

        # Verify tracklets can be listed via API
        t_res = c.get('/api/v1/tracklets?camera_id=test_cam_01', headers=headers)
        assert t_res.status_code == 200
        tracklets = t_res.json()
        assert len(tracklets) >= data["tracklets_count"]

        # Verify audit logs captured the inference event
        a_res = c.get('/api/v1/audit', headers=headers)
        assert a_res.status_code == 200
        actions = [log["action"] for log in a_res.json()]
        assert "inference.video" in actions
