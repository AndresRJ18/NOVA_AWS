"""Health check serverless function for Vercel deployment.

This module provides a health check endpoint to monitor Nova Sonic service
availability and overall system health.

Requirements: 12.2, 13.3
"""

from fastapi import FastAPI, Request
from mangum import Mangum
from datetime import datetime
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mock_interview_coach.voice_interface.nova_sonic_client import NovaSonicClient
from api.rate_limiter import RateLimiter

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="[%(levelname)s] %(asctime)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Nova Sonic Voice Health Check")

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


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Health status with Nova Sonic availability
        
    Requirements: 12.2, 13.3
    """
    try:
        # Check if dev mode is enabled
        dev_mode = os.getenv("ENABLE_DEV_MODE", "false").lower() == "true"
        
        if dev_mode:
            logger.info("Health check: dev mode enabled, skipping Nova Sonic check")
            return {
                "status": "healthy",
                "mode": "development",
                "nova_sonic": "mocked",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Check Nova Sonic availability
        client = NovaSonicClient()
        is_available = await client.health_check()
        
        status = "healthy" if is_available else "degraded"
        nova_status = "available" if is_available else "unavailable"
        
        logger.info(f"Health check: status={status}, nova_sonic={nova_status}")
        
        return {
            "status": status,
            "mode": "production",
            "nova_sonic": nova_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "mode": "production",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, 503


# Mangum handler for Vercel
handler = Mangum(app, lifespan="off")
