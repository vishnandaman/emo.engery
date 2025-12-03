"""
Main FastAPI application entry point.

This file initializes the FastAPI application, includes routers,
and sets up middleware for CORS and error handling.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import auth, contents

# Create database tables on startup
# In production, use Alembic migrations instead
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app with metadata
app = FastAPI(
    title="Content Management API",
    description="A RESTful API for content management with text summarization and sentiment analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS (Cross-Origin Resource Sharing)
# Allows frontend applications to make requests to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers (API endpoints)
# These are modular route handlers organized by feature
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(contents.router, prefix="/api", tags=["Content Management"])


@app.get("/")
async def root():
    """
    Root endpoint - health check.
    
    Returns:
        dict: A simple message indicating the API is running
    """
    return {
        "message": "Intelligent Content API is running",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        dict: Status of the API service
    """
    return {"status": "healthy", "service": "content-api"}

