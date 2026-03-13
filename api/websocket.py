"""WebSocket serverless function for Vercel deployment.

This module provides the WebSocket endpoint for real-time voice communication
between the client and the Nova Sonic voice interface.

Requirements: 8.1, 8.2, 12.4, 13.2
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from mangum import Mangum
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mock_interview_coach.voice_interface.websocket_handler import WebSocketHandler
from api.rate_limiter import RateLimiter

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="[%(levelname)s] %(asctime)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Nova Sonic Voice WebSocket")

# Initialize rate limiter (100 requests per 60 seconds by default)
rate_limiter = RateLimiter(
    max_requests=int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "100")),
    window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware for HTTP requests.
    
    Requirements: 13.4
    """
    await rate_limiter.check_rate_limit(request)
    response = await call_next(request)
    return response


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for voice communication.
    
    Args:
        websocket: WebSocket connection
        session_id: Unique session identifier
        
    Requirements: 8.1, 8.2
    """
    handler = WebSocketHandler()
    
    try:
        logger.info(f"WebSocket connection request: session_id={session_id}")
        await handler.handle_connection(websocket, session_id)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: session_id={session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: session_id={session_id}, error={str(e)}")
        raise


@app.get("/")
async def root():
    """Root endpoint for WebSocket service."""
    return {
        "service": "Nova Sonic Voice WebSocket",
        "status": "running",
        "endpoint": "/ws/{session_id}"
    }


# Mangum handler for Vercel
handler = Mangum(app, lifespan="off")
