from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, database
from datetime import datetime
import json
from typing import Dict, Any, List, Optional

router = APIRouter(prefix="/api")

# Get database session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Sessions endpoints
@router.post("/sessions/start", status_code=201)
def start_session(session_data: Dict[str, Any], db: Session = Depends(get_db)):
    """Start a new gameplay session"""
    db_session = models.GameSession(
        session_id=session_data.get("session_id"),
        player_id=session_data.get("player_id"),
        device_info=session_data.get("device_info"),
        start_time=datetime.utcnow()
    )
    db.add(db_session)
    try:
        db.commit()
        db.refresh(db_session)
        return {
            "session_id": db_session.session_id,
            "player_id": db_session.player_id,
            "device_info": db_session.device_info,
            "start_time": db_session.start_time,
            "end_time": db_session.end_time,
            "duration_seconds": db_session.duration_seconds
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create session: {str(e)}"
        )

@router.post("/sessions/end")
def end_session(session_data: Dict[str, Any], db: Session = Depends(get_db)):
    """End an existing gameplay session"""
    session_id = session_data.get("session_id")
    db_session = db.query(models.GameSession).filter(models.GameSession.session_id == session_id).first()
    if not db_session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )
    
    # End the session
    end_time_str = session_data.get("end_time")
    if end_time_str:
        try:
            end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
        except:
            end_time = datetime.utcnow()
    else:
        end_time = datetime.utcnow()
    
    db_session.end_time = end_time
    
    # Calculate session duration in seconds
    if db_session.start_time:
        duration = (db_session.end_time - db_session.start_time).total_seconds()
        db_session.duration_seconds = int(duration)
    
    db.commit()
    db.refresh(db_session)
    
    return {
        "session_id": db_session.session_id,
        "player_id": db_session.player_id,
        "device_info": db_session.device_info,
        "start_time": db_session.start_time,
        "end_time": db_session.end_time,
        "duration_seconds": db_session.duration_seconds
    }

# Events endpoints
@router.post("/events", status_code=201)
def create_event(event_data: Dict[str, Any], db: Session = Depends(get_db)):
    """Log a single gameplay event"""
    # Verify the session exists
    session_id = event_data.get("session_id")
    session = db.query(models.GameSession).filter(models.GameSession.session_id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )
    
    # Process timestamp
    timestamp_str = event_data.get("timestamp")
    if timestamp_str:
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            timestamp = datetime.utcnow()
    else:
        timestamp = datetime.utcnow()
    
    # Create event
    db_event = models.GameEvent(
        session_id=session_id,
        event_type=event_data.get("event_type"),
        event_name=event_data.get("event_name"),
        timestamp=timestamp,
        level_id=event_data.get("level_id"),
        position_x=event_data.get("position_x"),
        position_y=event_data.get("position_y"),
        position_z=event_data.get("position_z"),
        details=json.dumps(event_data.get("details")) if event_data.get("details") else None
    )
    
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    return {
        "id": db_event.id,
        "session_id": db_event.session_id,
        "event_type": db_event.event_type,
        "event_name": db_event.event_name,
        "timestamp": db_event.timestamp,
        "level_id": db_event.level_id,
        "position_x": db_event.position_x,
        "position_y": db_event.position_y,
        "position_z": db_event.position_z,
        "details": db_event.details
    }

@router.post("/events/batch", status_code=201)
def create_events_batch(batch_data: Dict[str, List[Dict[str, Any]]], db: Session = Depends(get_db)):
    """Log multiple gameplay events in a single request"""
    events = batch_data.get("events", [])
    
    # Validate all session IDs exist before processing
    session_ids = {event.get("session_id") for event in events}
    db_sessions = db.query(models.GameSession).filter(models.GameSession.session_id.in_(session_ids)).all()
    found_sessions = {session.session_id for session in db_sessions}
    
    missing_sessions = session_ids - found_sessions
    if missing_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Sessions not found: {missing_sessions}"
        )
    
    # Process all events
    for event_data in events:
        # Process timestamp
        timestamp_str = event_data.get("timestamp")
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                timestamp = datetime.utcnow()
        else:
            timestamp = datetime.utcnow()
            
        db_event = models.GameEvent(
            session_id=event_data.get("session_id"),
            event_type=event_data.get("event_type"),
            event_name=event_data.get("event_name"),
            timestamp=timestamp,
            level_id=event_data.get("level_id"),
            position_x=event_data.get("position_x"),
            position_y=event_data.get("position_y"),
            position_z=event_data.get("position_z"),
            details=json.dumps(event_data.get("details")) if event_data.get("details") else None
        )
        db.add(db_event)
    
    db.commit()
    return {"message": f"Successfully created {len(events)} events"}

# Metrics endpoints
@router.post("/metrics", status_code=201)
def create_metric(metric_data: Dict[str, Any], db: Session = Depends(get_db)):
    """Log a single gameplay metric"""
    # Verify the session exists
    session_id = metric_data.get("session_id")
    session = db.query(models.GameSession).filter(models.GameSession.session_id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )
    
    # Process timestamp
    timestamp_str = metric_data.get("timestamp")
    if timestamp_str:
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            timestamp = datetime.utcnow()
    else:
        timestamp = datetime.utcnow()
    
    # Create metric
    db_metric = models.GameMetric(
        session_id=session_id,
        metric_name=metric_data.get("metric_name"),
        metric_value=float(metric_data.get("metric_value", 0)),
        timestamp=timestamp,
        level_id=metric_data.get("level_id")
    )
    
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    
    return {
        "id": db_metric.id,
        "session_id": db_metric.session_id,
        "metric_name": db_metric.metric_name,
        "metric_value": db_metric.metric_value,
        "timestamp": db_metric.timestamp,
        "level_id": db_metric.level_id
    }

@router.post("/metrics/batch", status_code=201)
def create_metrics_batch(batch_data: Dict[str, List[Dict[str, Any]]], db: Session = Depends(get_db)):
    """Log multiple gameplay metrics in a single request"""
    metrics = batch_data.get("metrics", [])
    
    # Validate all session IDs exist before processing
    session_ids = {metric.get("session_id") for metric in metrics}
    db_sessions = db.query(models.GameSession).filter(models.GameSession.session_id.in_(session_ids)).all()
    found_sessions = {session.session_id for session in db_sessions}
    
    missing_sessions = session_ids - found_sessions
    if missing_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Sessions not found: {missing_sessions}"
        )
    
    # Process all metrics
    for metric_data in metrics:
        # Process timestamp
        timestamp_str = metric_data.get("timestamp")
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                timestamp = datetime.utcnow()
        else:
            timestamp = datetime.utcnow()
            
        db_metric = models.GameMetric(
            session_id=metric_data.get("session_id"),
            metric_name=metric_data.get("metric_name"),
            metric_value=float(metric_data.get("metric_value", 0)),
            timestamp=timestamp,
            level_id=metric_data.get("level_id")
        )
        db.add(db_metric)
    
    db.commit()
    return {"message": f"Successfully created {len(metrics)} metrics"}
