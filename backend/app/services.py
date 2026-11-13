from datetime import datetime
from uuid import uuid4
from sqlalchemy.exc import IntegrityError
from .models import AuditLog,DetectionEvent
def audit(db,actor,action,resource,detail): db.add(AuditLog(id=str(uuid4()),actor=actor,action=action,resource=resource,detail=detail))
def ingest_event(db,event,actor):
 """Idempotency key is event.id; duplicate delivery returns existing record."""
 existing=db.get(DetectionEvent,event.id)
 if existing:return existing,False
 row=DetectionEvent(id=event.id,camera_id=event.camera_id,occurred_at=event.occurred_at,payload={'event_type':event.event_type,**event.payload}); db.add(row); audit(db,actor,'event.ingest',f'events/{event.id}',{'camera_id':event.camera_id}); db.commit(); return row,True
