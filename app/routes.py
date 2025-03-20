from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import models, schemas, database
from typing import List
from datetime import datetime

router = APIRouter(prefix="/api")

# Sessions endpoints
@router.post("/sessions/start", response_model=schemas.SessionResponse, status_code=status.HTTP_201_CREATED)
def start_session(session: schemas.SessionStart, db: Session = Depends(database.get_db)):
    """Start a new gameplay session"""
    db_session = models.GameSession(
        session_id=session.session_id,
        player_id=session.player_id,
        device_info=session.device_info,
        start_time=datetime.utcnow()
    )
    db.add(db_session)
    try:
        db.commit()
        db.refresh(db_session)
        return db_session
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create session: {str(e)}"
        )

@router.post("/sessions/end", response_model=schemas.SessionResponse)
def end_session(session_end: schemas.SessionEnd, db: Session = Depends(database.get_db)):
    """End an existing gameplay session"""
    db_session = db.query(models.GameSession).filter(models.GameSession.session_id == session_end.session_id).first()
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Use the provided end_time or default to current time
    db_session.end_time = session_end.end_time if session_end.end_time else datetime.utcnow()
    
    # Calculate session duration in seconds
    if db_session.start_time:
        duration = (db_session.end_time - db_session.start_time).total_seconds()
        db_session.duration_seconds = int(duration)
    
    db.commit()
    db.refresh(db_session)
    return db_session

# Events endpoints
@router.post("/events", response_model=schemas.EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(event: schemas.EventCreate, db: Session = Depends(database.get_db)):
    """Log a single gameplay event"""
    # Verify the session exists
    session = db.query(models.GameSession).filter(models.GameSession.session_id == event.session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    db_event = models.GameEvent(
        session_id=event.session_id,
        event_type=event.event_type,
        event_name=event.event_name,
        timestamp=event.timestamp if event.timestamp else datetime.utcnow(),
        level_id=event.level_id,
        position_x=event.position_x,
        position_y=event.position_y,
        position_z=event.position_z,
        details=str(event.details) if event.details else None
    )
    
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@router.post("/events/batch", status_code=status.HTTP_201_CREATED)
def create_events_batch(batch: schemas.BatchEvents, db: Session = Depends(database.get_db)):
    """Log multiple gameplay events in a single request"""
    # Validate all session IDs exist before processing
    session_ids = {event.session_id for event in batch.events}
    db_sessions = db.query(models.GameSession).filter(models.GameSession.session_id.in_(session_ids)).all()
    found_sessions = {session.session_id for session in db_sessions}
    
    missing_sessions = session_ids - found_sessions
    if missing_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sessions not found: {missing_sessions}"
        )
    
    # Process all events
    for event in batch.events:
        db_event = models.GameEvent(
            session_id=event.session_id,
            event_type=event.event_type,
            event_name=event.event_name,
            timestamp=event.timestamp if event.timestamp else datetime.utcnow(),
            level_id=event.level_id,
            position_x=event.position_x,
            position_y=event.position_y,
            position_z=event.position_z,
            details=str(event.details) if event.details else None
        )
        db.add(db_event)
    
    db.commit()
    return {"message": f"Successfully created {len(batch.events)} events"}

# Metrics endpoints
@router.post("/metrics", response_model=schemas.MetricResponse, status_code=status.HTTP_201_CREATED)
def create_metric(metric: schemas.MetricCreate, db: Session = Depends(database.get_db)):
    """Log a single gameplay metric"""
    # Verify the session exists
    session = db.query(models.GameSession).filter(models.GameSession.session_id == metric.session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    db_metric = models.GameMetric(
        session_id=metric.session_id,
        metric_name=metric.metric_name,
        metric_value=metric.metric_value,
        timestamp=metric.timestamp if metric.timestamp else datetime.utcnow(),
        level_id=metric.level_id
    )
    
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    return db_metric

@router.post("/metrics/batch", status_code=status.HTTP_201_CREATED)
def create_metrics_batch(batch: schemas.BatchMetrics, db: Session = Depends(database.get_db)):
    """Log multiple gameplay metrics in a single request"""
    # Validate all session IDs exist before processing
    session_ids = {metric.session_id for metric in batch.metrics}
    db_sessions = db.query(models.GameSession).filter(models.GameSession.session_id.in_(session_ids)).all()
    found_sessions = {session.session_id for session in db_sessions}
    
    missing_sessions = session_ids - found_sessions
    if missing_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sessions not found: {missing_sessions}"
        )
    
    # Process all metrics
    for metric in batch.metrics:
        db_metric = models.GameMetric(
            session_id=metric.session_id,
            metric_name=metric.metric_name,
            metric_value=metric.metric_value,
            timestamp=metric.timestamp if metric.timestamp else datetime.utcnow(),
            level_id=metric.level_id
        )
        db.add(db_metric)
    
    db.commit()
    return {"message": f"Successfully created {len(batch.metrics)} metrics"}
