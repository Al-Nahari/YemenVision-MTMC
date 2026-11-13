from datetime import datetime
from uuid import uuid4
from fastapi import FastAPI,Depends,HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from .database import Base,engine,session
from .models import Camera,DetectionEvent,TrafficAggregate,ModelVersion,AuditLog
from .schemas import CameraIn,EventIn,TrafficQuery,ModelIn
from .security import require,rate_limit
from .services import audit,ingest_event
app=FastAPI(title='YemenVision Traffic Platform',version='0.1.0',openapi_url='/api/v1/openapi.json',docs_url='/api/v1/docs')
@app.on_event('startup')
def init(): Base.metadata.create_all(engine)
@app.get('/health')
def health(): return {'status':'ok','service':'traffic-platform'}
@app.post('/api/v1/cameras',status_code=201,dependencies=[Depends(rate_limit)])
def create_camera(body:CameraIn,user=Depends(require('admin','operator')),db:Session=Depends(session)):
 if db.get(Camera,body.id): raise HTTPException(409,'Camera already exists')
 db.add(Camera(**body.model_dump())); audit(db,user['subject'],'camera.create',f'cameras/{body.id}',{}); db.commit(); return body
@app.get('/api/v1/cameras',dependencies=[Depends(rate_limit)])
def cameras(user=Depends(require('admin','operator','analyst')),db:Session=Depends(session)): return list(db.scalars(select(Camera)).all())
@app.post('/api/v1/events',status_code=202,dependencies=[Depends(rate_limit)])
def events(body:EventIn,user=Depends(require('admin','operator')),db:Session=Depends(session)):
 if not db.get(Camera,body.camera_id): raise HTTPException(422,'Unknown camera_id')
 row,created=ingest_event(db,body,user['subject']); return {'id':row.id,'status':'accepted' if created else 'duplicate_ignored'}
@app.get('/api/v1/events',dependencies=[Depends(rate_limit)])
def list_events(camera_id:str|None=None,limit:int=100,offset:int=0,user=Depends(require('admin','operator','analyst')),db:Session=Depends(session)):
 if not 1<=limit<=1000: raise HTTPException(422,'limit must be 1..1000')
 q=select(DetectionEvent).order_by(DetectionEvent.occurred_at.desc()).offset(offset).limit(limit)
 if camera_id:q=q.where(DetectionEvent.camera_id==camera_id)
 return list(db.scalars(q).all())
@app.get('/api/v1/traffic',dependencies=[Depends(rate_limit)])
def traffic(camera_id:str|None=None,limit:int=100,user=Depends(require('admin','operator','analyst')),db:Session=Depends(session)):
 q=select(TrafficAggregate).order_by(TrafficAggregate.bucket_start.desc()).limit(min(limit,1000));
 if camera_id:q=q.where(TrafficAggregate.camera_id==camera_id)
 return list(db.scalars(q).all())
@app.post('/api/v1/models',status_code=201,dependencies=[Depends(rate_limit)])
def model(body:ModelIn,user=Depends(require('admin')),db:Session=Depends(session)):
 if db.get(ModelVersion,body.id):raise HTTPException(409,'Model id exists')
 db.add(ModelVersion(**body.model_dump())); audit(db,user['subject'],'model.register',f'models/{body.id}',{});db.commit();return body
@app.get('/api/v1/audit',dependencies=[Depends(rate_limit)])
def audit_log(limit:int=100,user=Depends(require('admin')),db:Session=Depends(session)):return list(db.scalars(select(AuditLog).order_by(AuditLog.occurred_at.desc()).limit(min(limit,1000))).all())
