from datetime import datetime
from pydantic import BaseModel,Field,field_validator
class CameraIn(BaseModel): id:str=Field(pattern=r'^[A-Za-z0-9_-]{1,64}$'); zone:str|None=None; direction:str|None=None; active:bool=True
class EventIn(BaseModel): id:str=Field(pattern=r'^[A-Za-z0-9_-]{8,128}$'); camera_id:str; occurred_at:datetime; event_type:str; payload:dict=Field(default_factory=dict)
class TrafficQuery(BaseModel): camera_id:str|None=None; start:datetime|None=None; end:datetime|None=None; limit:int=Field(default=100,ge=1,le=1000); offset:int=Field(default=0,ge=0)
class ModelIn(BaseModel): id:str; stage:str; version:str; artifact_uri:str; metadata_json:dict=Field(default_factory=dict)
