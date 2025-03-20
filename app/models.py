from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class GameSession(Base):
    """Represents a single gameplay session"""
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    player_id = Column(String, index=True)
    device_info = Column(String)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Relationships
    events = relationship("GameEvent", back_populates="session")
    metrics = relationship("GameMetric", back_populates="session")

class GameEvent(Base):
    """Represents a gameplay event (actions, achievements, etc.)"""
    __tablename__ = "game_events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("game_sessions.session_id"))
    event_type = Column(String, index=True)
    event_name = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level_id = Column(String, nullable=True)
    position_x = Column(Float, nullable=True)
    position_y = Column(Float, nullable=True)
    position_z = Column(Float, nullable=True)
    details = Column(Text, nullable=True)  # JSON data can be stored here
    
    # Relationships
    session = relationship("GameSession", back_populates="events")

class GameMetric(Base):
    """Represents numerical gameplay metrics (scores, times, resources, etc.)"""
    __tablename__ = "game_metrics"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("game_sessions.session_id"))
    metric_name = Column(String, index=True)
    metric_value = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level_id = Column(String, nullable=True)
    
    # Relationships
    session = relationship("GameSession", back_populates="metrics")
