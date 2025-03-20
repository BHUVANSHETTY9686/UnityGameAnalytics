from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import models, database
from .database import engine
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Unity Game Analytics API",
    description="API for logging and analyzing gameplay data from Unity games",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes after app is created to avoid circular imports
from .routes_simple import router
app.include_router(router)

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "Welcome to Unity Game Analytics API",
        "docs": "/docs",
        "version": "1.0.0"
    }

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
