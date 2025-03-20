from flask import Flask, request, jsonify
import sqlite3
import os
import json
from datetime import datetime
import uuid
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
app.logger.info(f"Flask version: {Flask.__version__}")
app.logger.info("Starting Unity Game Analytics API")

# Helper function to get database connection
def get_db_connection():
    conn = sqlite3.connect('analytics.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS game_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            player_id TEXT,
            device_info TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            duration_seconds INTEGER
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS game_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            event_type TEXT,
            event_name TEXT,
            timestamp TIMESTAMP,
            level_id TEXT,
            position_x REAL,
            position_y REAL,
            position_z REAL,
            details TEXT,
            FOREIGN KEY (session_id) REFERENCES game_sessions (session_id)
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS game_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            metric_name TEXT,
            metric_value REAL,
            timestamp TIMESTAMP,
            level_id TEXT,
            FOREIGN KEY (session_id) REFERENCES game_sessions (session_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Home route
@app.route('/')
def home():
    app.logger.info("Home route accessed")
    return jsonify({
        "message": "Welcome to Unity Game Analytics API",
        "version": "1.0.0"
    })

# Sessions routes
@app.route('/api/sessions/start', methods=['POST'])
def start_session():
    app.logger.info("Session start route accessed")
    data = request.json
    
    if not data or 'player_id' not in data:
        return jsonify({"error": "Missing player_id"}), 400
    
    session_id = data.get('session_id', str(uuid.uuid4()))
    player_id = data['player_id']
    device_info = data.get('device_info', '')
    start_time = datetime.utcnow().isoformat()
    
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO game_sessions (session_id, player_id, device_info, start_time) VALUES (?, ?, ?, ?)',
            (session_id, player_id, device_info, start_time)
        )
        conn.commit()
        
        return jsonify({
            "session_id": session_id,
            "player_id": player_id,
            "device_info": device_info,
            "start_time": start_time
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

@app.route('/api/sessions/end', methods=['POST'])
def end_session():
    app.logger.info("Session end route accessed")
    data = request.json
    
    if not data or 'session_id' not in data:
        return jsonify({"error": "Missing session_id"}), 400
    
    session_id = data['session_id']
    end_time = data.get('end_time', datetime.utcnow().isoformat())
    
    conn = get_db_connection()
    try:
        # Get session start time
        session = conn.execute('SELECT * FROM game_sessions WHERE session_id = ?', (session_id,)).fetchone()
        
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        # Parse timestamps
        start_time = datetime.fromisoformat(session['start_time'])
        if isinstance(end_time, str):
            try:
                end_time_obj = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except:
                end_time_obj = datetime.utcnow()
        else:
            end_time_obj = datetime.utcnow()
            
        # Calculate duration
        duration = int((end_time_obj - start_time).total_seconds())
        
        # Update session
        conn.execute(
            'UPDATE game_sessions SET end_time = ?, duration_seconds = ? WHERE session_id = ?',
            (end_time_obj.isoformat(), duration, session_id)
        )
        conn.commit()
        
        return jsonify({
            "session_id": session_id,
            "player_id": session['player_id'],
            "device_info": session['device_info'],
            "start_time": session['start_time'],
            "end_time": end_time_obj.isoformat(),
            "duration_seconds": duration
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

# Events routes
@app.route('/api/events', methods=['POST'])
def create_event():
    app.logger.info("Event creation route accessed")
    data = request.json
    
    if not data or 'session_id' not in data or 'event_type' not in data or 'event_name' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    session_id = data['session_id']
    event_type = data['event_type']
    event_name = data['event_name']
    level_id = data.get('level_id')
    position_x = data.get('position_x')
    position_y = data.get('position_y')
    position_z = data.get('position_z')
    details = json.dumps(data.get('details')) if data.get('details') else None
    timestamp = data.get('timestamp', datetime.utcnow().isoformat())
    
    conn = get_db_connection()
    try:
        # Check if session exists
        session = conn.execute('SELECT * FROM game_sessions WHERE session_id = ?', (session_id,)).fetchone()
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        # Insert event
        cursor = conn.execute(
            '''INSERT INTO game_events 
               (session_id, event_type, event_name, timestamp, level_id, position_x, position_y, position_z, details) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (session_id, event_type, event_name, timestamp, level_id, position_x, position_y, position_z, details)
        )
        conn.commit()
        
        event_id = cursor.lastrowid
        
        return jsonify({
            "id": event_id,
            "session_id": session_id,
            "event_type": event_type,
            "event_name": event_name,
            "timestamp": timestamp,
            "level_id": level_id,
            "position_x": position_x,
            "position_y": position_y,
            "position_z": position_z,
            "details": details
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

@app.route('/api/events/batch', methods=['POST'])
def create_events_batch():
    app.logger.info("Batch event creation route accessed")
    data = request.json
    
    if not data or 'events' not in data or not isinstance(data['events'], list):
        return jsonify({"error": "Missing events array"}), 400
    
    events = data['events']
    if not events:
        return jsonify({"message": "No events to process"}), 200
    
    # Extract session IDs
    session_ids = set(event.get('session_id') for event in events if 'session_id' in event)
    
    conn = get_db_connection()
    try:
        # Verify all sessions exist
        for session_id in session_ids:
            session = conn.execute('SELECT * FROM game_sessions WHERE session_id = ?', (session_id,)).fetchone()
            if not session:
                return jsonify({"error": f"Session not found: {session_id}"}), 404
        
        # Insert all events
        for event in events:
            if 'session_id' not in event or 'event_type' not in event or 'event_name' not in event:
                continue
                
            session_id = event['session_id']
            event_type = event['event_type']
            event_name = event['event_name']
            level_id = event.get('level_id')
            position_x = event.get('position_x')
            position_y = event.get('position_y')
            position_z = event.get('position_z')
            details = json.dumps(event.get('details')) if event.get('details') else None
            timestamp = event.get('timestamp', datetime.utcnow().isoformat())
            
            conn.execute(
                '''INSERT INTO game_events 
                   (session_id, event_type, event_name, timestamp, level_id, position_x, position_y, position_z, details) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (session_id, event_type, event_name, timestamp, level_id, position_x, position_y, position_z, details)
            )
        
        conn.commit()
        return jsonify({"message": f"Successfully created {len(events)} events"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

# Metrics routes
@app.route('/api/metrics', methods=['POST'])
def create_metric():
    app.logger.info("Metric creation route accessed")
    data = request.json
    
    if not data or 'session_id' not in data or 'metric_name' not in data or 'metric_value' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    session_id = data['session_id']
    metric_name = data['metric_name']
    try:
        metric_value = float(data['metric_value'])
    except (ValueError, TypeError):
        return jsonify({"error": "metric_value must be a number"}), 400
        
    level_id = data.get('level_id')
    timestamp = data.get('timestamp', datetime.utcnow().isoformat())
    
    conn = get_db_connection()
    try:
        # Check if session exists
        session = conn.execute('SELECT * FROM game_sessions WHERE session_id = ?', (session_id,)).fetchone()
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        # Insert metric
        cursor = conn.execute(
            'INSERT INTO game_metrics (session_id, metric_name, metric_value, timestamp, level_id) VALUES (?, ?, ?, ?, ?)',
            (session_id, metric_name, metric_value, timestamp, level_id)
        )
        conn.commit()
        
        metric_id = cursor.lastrowid
        
        return jsonify({
            "id": metric_id,
            "session_id": session_id,
            "metric_name": metric_name,
            "metric_value": metric_value,
            "timestamp": timestamp,
            "level_id": level_id
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

@app.route('/api/metrics/batch', methods=['POST'])
def create_metrics_batch():
    app.logger.info("Batch metric creation route accessed")
    data = request.json
    
    if not data or 'metrics' not in data or not isinstance(data['metrics'], list):
        return jsonify({"error": "Missing metrics array"}), 400
    
    metrics = data['metrics']
    if not metrics:
        return jsonify({"message": "No metrics to process"}), 200
    
    # Extract session IDs
    session_ids = set(metric.get('session_id') for metric in metrics if 'session_id' in metric)
    
    conn = get_db_connection()
    try:
        # Verify all sessions exist
        for session_id in session_ids:
            session = conn.execute('SELECT * FROM game_sessions WHERE session_id = ?', (session_id,)).fetchone()
            if not session:
                return jsonify({"error": f"Session not found: {session_id}"}), 404
        
        # Insert all metrics
        for metric in metrics:
            if 'session_id' not in metric or 'metric_name' not in metric or 'metric_value' not in metric:
                continue
                
            session_id = metric['session_id']
            metric_name = metric['metric_name']
            try:
                metric_value = float(metric['metric_value'])
            except (ValueError, TypeError):
                continue
                
            level_id = metric.get('level_id')
            timestamp = metric.get('timestamp', datetime.utcnow().isoformat())
            
            conn.execute(
                'INSERT INTO game_metrics (session_id, metric_name, metric_value, timestamp, level_id) VALUES (?, ?, ?, ?, ?)',
                (session_id, metric_name, metric_value, timestamp, level_id)
            )
        
        conn.commit()
        return jsonify({"message": f"Successfully created {len(metrics)} metrics"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(debug=True, host='0.0.0.0', port=port)
else:
    # This block runs when the app is imported by a WSGI server
    app.logger.info("Running as imported module - likely under WSGI")
