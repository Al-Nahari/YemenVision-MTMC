import os
os.environ['DATABASE_URL']='sqlite:///./test_platform.db'
os.environ['API_KEYS_JSON']='{"admin":{"subject":"tester","roles":["admin"]}}'
from fastapi.testclient import TestClient
from app.main import app
def test_auth_and_idempotent_events():
 with TestClient(app) as c:
  assert c.get('/api/v1/cameras').status_code==401
  h={'x-api-key':'admin'}
  assert c.post('/api/v1/cameras',json={'id':'cam-1'},headers=h).status_code in (201,409)
  payload={'id':'evt-00000001','camera_id':'cam-1','occurred_at':'2026-01-01T00:00:00Z','event_type':'detection','payload':{}}
  assert c.post('/api/v1/events',json=payload,headers=h).status_code==202
  assert c.post('/api/v1/events',json=payload,headers=h).json()['status']=='duplicate_ignored'
