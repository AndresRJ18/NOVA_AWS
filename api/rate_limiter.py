"""Rate limiting middleware for API endpoints.

This module provides rate limiting functionality to prevent abuse and excessive
API usage by tracking requests per client IP address.

Requirements: 13.4
"""

from fastapi import Request, HTTPException
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter that tracks requests per client IP address.
    
    Attributes:
        max_requests: Maximum number of requests allowed per window
        window_seconds: Time window in seconds for rate limiting
        requests: Dictionary tracking request timestamps per IP
        
    Requirements: 13.4
    """
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed per window (default: 100)
            window_seconds: Time window in seconds (default: 60)
        """
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests: Dict[str, List[datetime]] = defaultdict(list)
        
        logger.info(
            f"RateLimiter initialized: max_requests={max_requests}, "
            f"window_seconds={window_seconds}"
        )
    
    async def check_rate_limit(self, request: Request) -> None:
        """
        Check if the request exceeds rate limit.
        
        Args:
            request: FastAPI request object
            
        Raises:
            HTTPException: 429 status code if rate limit exceeded
            
        Requirements: 13.4
        """
        # Get client IP address
        client_ip = self._get_client_ip(request)
        now = datetime.now(timezone.utc)
        
        # Clean old requests outside the time window
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < self.window
        ]
        
        # Check if rate limit exceeded
        current_count = len(self.requests[client_ip])
        
        if current_count >= self.max_requests:
            logger.warning(
                f"Rate limit exceeded: client_ip={client_ip}, "
                f"requests={current_count}, max={self.max_requests}"
            )
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.max_requests} requests per "
                               f"{self.window.total_seconds()} seconds allowed",
                    "retry_after": int(self.window.total_seconds())
                }
            )
        
        # Record this request
        self.requests[client_ip].append(now)
        
        logger.debug(
            f"Rate limit check passed: client_ip={client_ip}, "
            f"requests={current_count + 1}/{self.max_requests}"
        )
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request.
        
        Handles X-Forwarded-For header for proxied requests (Vercel).
        
        Args:
            request: FastAPI request object
            
        Returns:
            Client IP address as string
        """
        # Check X-Forwarded-For header (Vercel uses this)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        # Fallback to direct client host
        return request.client.host if request.client else "unknown"
    
    def get_stats(self, client_ip: str = None) -> dict:
        """
        Get rate limiter statistics.
        
        Args:
            client_ip: Optional IP to get stats for specific client
            
        Returns:
            Dictionary with rate limiter statistics
        """
        if client_ip:
            now = datetime.now(timezone.utc)
            # Clean old requests
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if now - req_time < self.window
            ]
            
            return {
                "client_ip": client_ip,
                "current_requests": len(self.requests[client_ip]),
                "max_requests": self.max_requests,
                "window_seconds": int(self.window.total_seconds()),
                "remaining": max(0, self.max_requests - len(self.requests[client_ip]))
            }
        
        # Overall stats
        return {
            "total_tracked_ips": len(self.requests),
            "max_requests": self.max_requests,
            "window_seconds": int(self.window.total_seconds())
        }
    
    def reset(self, client_ip: str = None) -> None:
        """
        Reset rate limiter for a specific IP or all IPs.
        
        Args:
            client_ip: Optional IP to reset. If None, resets all.
        """
        if client_ip:
            if client_ip in self.requests:
                del self.requests[client_ip]
                logger.info(f"Rate limiter reset for client_ip={client_ip}")
        else:
            self.requests.clear()
            logger.info("Rate limiter reset for all clients")
