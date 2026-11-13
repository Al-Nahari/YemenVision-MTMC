from dataclasses import dataclass, field
from typing import Optional
@dataclass(frozen=True)
class Tracklet:
 local_track_id: int; camera_id: str; video_id: str; start_time: float; end_time: float
 embedding: Optional[list[float]]=None; vehicle_type: str='unknown'; color: str='unknown'; direction: str='unknown'; quality: str='unknown'; zone: str='unknown'
@dataclass(frozen=True)
class AssociationDecision:
 source: Tracklet; target: Tracklet; state: str # accepted_candidate|low_confidence|ambiguous|rejected|unknown
 score: float|None; evidence: dict; temporary_event_group: Optional[str]=None
