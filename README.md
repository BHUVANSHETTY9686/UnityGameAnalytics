# Unity Game Analytics API

A Python-based API server for logging and analyzing gameplay data from Unity games.

## Features

- RESTful API endpoints for logging various game events
- Stores analytics data in a SQLite database
- Easy integration with Unity games
- Configurable data retention and export options

## Setup and Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Start the server:
   ```
   uvicorn app.main:app --reload
   ```

## API Endpoints

- `POST /api/events`: Log a general gameplay event
- `POST /api/sessions`: Track gameplay sessions (start/end)
- `POST /api/metrics`: Record numeric metrics (scores, times, etc.)
- `GET /api/dashboard`: View analytics dashboard (basic UI)

## Unity Integration

See the [Unity Integration Guide](docs/unity_integration.md) for instructions on how to call this API from your Unity game.

## Configuration

Environment variables can be set in a `.env` file:

- `DATABASE_URL`: Database connection string (default: SQLite)
- `API_KEY`: Optional API key for securing endpoints
- `LOG_LEVEL`: Logging level (default: INFO)
