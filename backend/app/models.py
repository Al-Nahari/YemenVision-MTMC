from datetime import datetime

from sqlalchemy import JSON, DateTime, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Camera(Base):
 __tablename__='cameras'; id:Mapped[str]=mapped_column(String,primary_key=True); zone:Mapped[str|None]=mapped_column(String); direction:Mapped[str|None]=mapped_column(String); active:Mapped[bool]=mapped_column(default=True); stream_url:Mapped[str|None]=mapped_column(String, nullable=True)
class DetectionEvent(Base):
 __tablename__='detection_events'; id:Mapped[str]=mapped_column(String,primary_key=True); camera_id:Mapped[str]=mapped_column(String,index=True); occurred_at:Mapped[datetime]=mapped_column(DateTime,index=True); payload:Mapped[dict]=mapped_column(JSON); plate_text:Mapped[str|None]=mapped_column(String,nullable=True,index=True); __table_args__=(Index('ix_detection_camera_time','camera_id','occurred_at'),)
class Tracklet(Base):
 __tablename__='tracklets'; id:Mapped[str]=mapped_column(String,primary_key=True); camera_id:Mapped[str]=mapped_column(String,index=True); video_id:Mapped[str]=mapped_column(String,index=True); local_track_id:Mapped[int]; start_time:Mapped[datetime]=mapped_column(DateTime); end_time:Mapped[datetime]=mapped_column(DateTime); payload:Mapped[dict]=mapped_column(JSON); __table_args__=(UniqueConstraint('camera_id','video_id','local_track_id',name='uq_local_track'),Index('ix_track_camera_time','camera_id','start_time'))
class AssociationEvent(Base):
 __tablename__='association_events'; id:Mapped[str]=mapped_column(String,primary_key=True); occurred_at:Mapped[datetime]=mapped_column(DateTime,index=True); state:Mapped[str]=mapped_column(String,index=True); payload:Mapped[dict]=mapped_column(JSON)
class TrafficAggregate(Base):
 __tablename__='traffic_aggregates'; id:Mapped[str]=mapped_column(String,primary_key=True); camera_id:Mapped[str]=mapped_column(String,index=True); bucket_start:Mapped[datetime]=mapped_column(DateTime,index=True); granularity:Mapped[str]=mapped_column(String); payload:Mapped[dict]=mapped_column(JSON); __table_args__=(Index('ix_traffic_camera_bucket','camera_id','bucket_start'),)
class AuditLog(Base):
 __tablename__='audit_logs'; id:Mapped[str]=mapped_column(String,primary_key=True); occurred_at:Mapped[datetime]=mapped_column(DateTime,index=True,default=datetime.utcnow); actor:Mapped[str]=mapped_column(String,index=True); action:Mapped[str]=mapped_column(String); resource:Mapped[str]=mapped_column(String); detail:Mapped[dict]=mapped_column(JSON)
class ProcessedVideo(Base):
 __tablename__='processed_videos'; id:Mapped[str]=mapped_column(String,primary_key=True); file_name:Mapped[str]=mapped_column(String,unique=True,index=True); original_name:Mapped[str]=mapped_column(String); video_id:Mapped[str]=mapped_column(String,index=True); camera_id:Mapped[str|None]=mapped_column(String,index=True,nullable=True); created_at:Mapped[datetime]=mapped_column(DateTime,index=True); frames_processed:Mapped[int]=mapped_column(default=0); duration_seconds:Mapped[float]=mapped_column(default=0.0); file_size:Mapped[int]=mapped_column(default=0); model_version:Mapped[str|None]=mapped_column(String,nullable=True); plate_count:Mapped[int]=mapped_column(default=0); source:Mapped[str]=mapped_column(default='upload'); __table_args__=(Index('ix_video_camera_created','camera_id','created_at'),)
class ModelVersion(Base):
 __tablename__='model_versions'; id:Mapped[str]=mapped_column(String,primary_key=True); stage:Mapped[str]=mapped_column(String,index=True); version:Mapped[str]=mapped_column(String); artifact_uri:Mapped[str]=mapped_column(String); metadata_json:Mapped[dict]=mapped_column(JSON); __table_args__=(UniqueConstraint('stage','version',name='uq_model_version'),)
