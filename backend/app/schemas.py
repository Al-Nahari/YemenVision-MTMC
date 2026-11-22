from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field, field_validator

class CameraIn(BaseModel):
    id: str = Field(pattern=r'^[A-Za-z0-9_-]{1,64}$')
    zone: Optional[str] = None
    direction: Optional[str] = None
    active: bool = True
    stream_url: Optional[str] = Field(default=None, max_length=2048)

    @field_validator('stream_url')
    @classmethod
    def validate_stream_url(cls, value):
        if value and not value.lower().startswith(('rtsp://', 'rtsps://', 'http://', 'https://')):
            raise ValueError('stream_url must use RTSP, RTSPS, HTTP, or HTTPS')
        return value

class EventIn(BaseModel):
    id: str = Field(pattern=r'^[A-Za-z0-9_-]{8,128}$')
    camera_id: str
    occurred_at: datetime
    event_type: str
    payload: dict = Field(default_factory=dict)

class TrafficQuery(BaseModel):
    camera_id: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

class ModelIn(BaseModel):
    id: str
    stage: str
    version: str
    artifact_uri: str
    metadata_json: dict = Field(default_factory=dict)

class TrackletOut(BaseModel):
    id: str
    camera_id: str
    video_id: str
    local_track_id: int
    start_time: datetime
    end_time: datetime
    payload: dict = Field(default_factory=dict)

class InferenceVideoRequest(BaseModel):
    camera_id: str
    video_path: str
    conf_threshold: float = Field(default=0.25, ge=0.05, le=0.95)
    iou_threshold: float = Field(default=0.3, ge=0.1, le=0.9)
    max_frames: Optional[int] = Field(default=None, ge=1)

class InferenceVideoResponse(BaseModel):
    status: str
    camera_id: str
    video_id: str
    frames_processed: int
    tracklets_count: int
    events_count: int
    duration_seconds: float
    model_version: str
    video_url: Optional[str] = None

class DetectionItem(BaseModel):
    box: List[float]
    confidence: float
    class_id: int
    class_name: str

class InferenceFrameRequest(BaseModel):
    camera_id: str
    detections: List[DetectionItem]
    frame_index: int = 0
    timestamp: Optional[datetime] = None

class InferenceFrameResponse(BaseModel):
    camera_id: str
    frame_index: int
    events_generated: int
    active_tracks: int
