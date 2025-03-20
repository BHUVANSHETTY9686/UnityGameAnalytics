from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

# Session schemas
class SessionBase(BaseModel):
    player_id: str
    device_info: Optional[str] = None

class SessionStart(SessionBase):
    session_id: str

class SessionEnd(BaseModel):
    session_id: str
    end_time: datetime = None

    class Config:
        arbitrary_types_allowed = True

class SessionResponse(SessionBase):
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

# Event schemas
class EventCreate(BaseModel):
    session_id: str
    event_type: str
    event_name: str
    level_id: Optional[str] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    position_z: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = None

    class Config:
        arbitrary_types_allowed = True

class EventResponse(EventCreate):
    id: int

    class Config:
        orm_mode = True

# Metric schemas
class MetricCreate(BaseModel):
    session_id: str
    metric_name: str
    metric_value: float
    level_id: Optional[str] = None
    timestamp: datetime = None

    class Config:
        arbitrary_types_allowed = True

class MetricResponse(MetricCreate):
    id: int

    class Config:
        orm_mode = True

# Batch upload schemas
class BatchEvents(BaseModel):
    events: List[EventCreate]

class BatchMetrics(BaseModel):
    metrics: List[MetricCreate]
