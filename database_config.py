import os
import sqlite3
from urllib.parse import urlparse

# Database configuration
DB_URL = os.environ.get('DATABASE_URL', 'sqlite:///analytics.db')

def get_db_connection():
    """Get database connection based on environment"""
    if DB_URL.startswith('sqlite'):
        conn = sqlite3.connect('analytics.db')
        conn.row_factory = sqlite3.Row
        return conn
    elif DB_URL.startswith('postgres'):
        # For PostgreSQL deployment (uncomment and pip install psycopg2-binary)
        # import psycopg2
        # from psycopg2.extras import RealDictCursor
        # url = urlparse(DB_URL)
        # dbname = url.path[1:]
        # user = url.username
        # password = url.password
        # host = url.hostname
        # port = url.port
        # conn = psycopg2.connect(
        #     dbname=dbname,
        #     user=user,
        #     password=password,
        #     host=host,
        #     port=port,
        #     cursor_factory=RealDictCursor
        # )
        # return conn
        raise NotImplementedError("PostgreSQL support requires psycopg2-binary package")
    else:
        raise ValueError(f"Unsupported database URL: {DB_URL}")
