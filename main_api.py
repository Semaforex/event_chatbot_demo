"""
Main FastAPI application that includes the api_highlevel router.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging

# Import your router
from api.api_highlevel import router as highlevel_router

# Load environment variables
load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Event Chatbot API",
    description="Event chatbot with async message processing",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your router
app.include_router(highlevel_router, prefix="/api/v1", tags=["chat"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Event Chatbot API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Event Chatbot API"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
