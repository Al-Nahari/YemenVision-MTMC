from dataclasses import dataclass,asdict
from datetime import datetime
from typing import Optional
import hashlib
@dataclass(frozen=True)
class TrafficEvent:
 camera_id:str; timestamp:datetime; vehicle_class:str; direction:str; local_track_id:int; detection_confidence:float; event_type:str
 lane:Optional[str]=None; zone:Optional[str]=None; quality_flags:tuple[str,...]=()
 def event_id(self):
  raw=f'{self.camera_id}|{self.timestamp.isoformat()}|{self.local_track_id}|{self.event_type}'
  return 'evt_'+hashlib.sha256(raw.encode()).hexdigest()[:20]
 def to_dict(self):
  d=asdict(self); d['timestamp']=self.timestamp.isoformat(); d['event_id']=self.event_id(); return d
