"""Unit tests for RateLimiter class.

Tests rate limiting functionality including request tracking, limit enforcement,
and IP address extraction.

Requirements: 13.4
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, MagicMock
from fastapi import HTTPException, Request
from api.rate_limiter import RateLimiter


class TestRateLimiter:
    """Test suite for RateLimiter class."""
    
    def test_initialization_default_values(self):
        """Test RateLimiter initializes with default values."""
        limiter = RateLimiter()
        
        assert limiter.max_requests == 100
        assert limiter.window == timedelta(seconds=60)
        assert len(limiter.requests) == 0
    
    def test_initialization_custom_values(self):
        """Test RateLimiter initializes with custom values."""
        limiter = RateLimiter(max_requests=50, window_seconds=30)
        
        assert limiter.max_requests == 50
        assert limiter.window == timedelta(seconds=30)
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_allows_first_request(self):
        """Test that first request from IP is allowed."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        request = self._create_mock_request("192.168.1.1")
        
        # Should not raise exception
        await limiter.check_rate_limit(request)
        
        assert len(limiter.requests["192.168.1.1"]) == 1
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_allows_within_limit(self):
        """Test that requests within limit are allowed."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        request = self._create_mock_request("192.168.1.1")
        
        # Make 5 requests (at the limit)
        for _ in range(5):
            await limiter.check_rate_limit(request)
        
        assert len(limiter.requests["192.168.1.1"]) == 5
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_blocks_exceeding_limit(self):
        """Test that requests exceeding limit are blocked with 429."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        request = self._create_mock_request("192.168.1.1")
        
        # Make 3 requests (at the limit)
        for _ in range(3):
            await limiter.check_rate_limit(request)
        
        # 4th request should be blocked
        with pytest.raises(HTTPException) as exc_info:
            await limiter.check_rate_limit(request)
        
        assert exc_info.value.status_code == 429
        assert "Rate limit exceeded" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_tracks_multiple_ips(self):
        """Test that rate limiter tracks multiple IPs independently."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        request1 = self._create_mock_request("192.168.1.1")
        request2 = self._create_mock_request("192.168.1.2")
        
        # Make 2 requests from each IP
        await limiter.check_rate_limit(request1)
        await limiter.check_rate_limit(request1)
        await limiter.check_rate_limit(request2)
        await limiter.check_rate_limit(request2)
        
        assert len(limiter.requests["192.168.1.1"]) == 2
        assert len(limiter.requests["192.168.1.2"]) == 2
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_cleans_old_requests(self):
        """Test that old requests outside window are cleaned up."""
        limiter = RateLimiter(max_requests=3, window_seconds=1)
        request = self._create_mock_request("192.168.1.1")
        
        # Add old request manually
        old_time = datetime.now(timezone.utc) - timedelta(seconds=2)
        limiter.requests["192.168.1.1"].append(old_time)
        
        # Make new request
        await limiter.check_rate_limit(request)
        
        # Old request should be cleaned, only new one remains
        assert len(limiter.requests["192.168.1.1"]) == 1
        assert limiter.requests["192.168.1.1"][0] > old_time
    
    def test_get_client_ip_from_direct_connection(self):
        """Test extracting IP from direct connection."""
        limiter = RateLimiter()
        request = self._create_mock_request("192.168.1.1")
        
        ip = limiter._get_client_ip(request)
        
        assert ip == "192.168.1.1"
    
    def test_get_client_ip_from_x_forwarded_for(self):
        """Test extracting IP from X-Forwarded-For header (Vercel)."""
        limiter = RateLimiter()
        request = self._create_mock_request(
            "10.0.0.1",
            headers={"X-Forwarded-For": "203.0.113.1, 198.51.100.1"}
        )
        
        ip = limiter._get_client_ip(request)
        
        # Should return first IP in chain
        assert ip == "203.0.113.1"
    
    def test_get_client_ip_handles_missing_client(self):
        """Test handling request with no client info."""
        limiter = RateLimiter()
        request = Mock(spec=Request)
        request.client = None
        request.headers = {}
        
        ip = limiter._get_client_ip(request)
        
        assert ip == "unknown"
    
    def test_get_stats_for_specific_ip(self):
        """Test getting statistics for specific IP."""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        
        # Add some requests manually
        now = datetime.now(timezone.utc)
        limiter.requests["192.168.1.1"] = [now, now, now]
        
        stats = limiter.get_stats("192.168.1.1")
        
        assert stats["client_ip"] == "192.168.1.1"
        assert stats["current_requests"] == 3
        assert stats["max_requests"] == 10
        assert stats["window_seconds"] == 60
        assert stats["remaining"] == 7
    
    def test_get_stats_overall(self):
        """Test getting overall statistics."""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        
        # Add requests for multiple IPs
        now = datetime.now(timezone.utc)
        limiter.requests["192.168.1.1"] = [now]
        limiter.requests["192.168.1.2"] = [now]
        
        stats = limiter.get_stats()
        
        assert stats["total_tracked_ips"] == 2
        assert stats["max_requests"] == 10
        assert stats["window_seconds"] == 60
    
    def test_reset_specific_ip(self):
        """Test resetting rate limiter for specific IP."""
        limiter = RateLimiter()
        
        # Add requests for multiple IPs
        now = datetime.now(timezone.utc)
        limiter.requests["192.168.1.1"] = [now]
        limiter.requests["192.168.1.2"] = [now]
        
        limiter.reset("192.168.1.1")
        
        assert "192.168.1.1" not in limiter.requests
        assert "192.168.1.2" in limiter.requests
    
    def test_reset_all_ips(self):
        """Test resetting rate limiter for all IPs."""
        limiter = RateLimiter()
        
        # Add requests for multiple IPs
        now = datetime.now(timezone.utc)
        limiter.requests["192.168.1.1"] = [now]
        limiter.requests["192.168.1.2"] = [now]
        
        limiter.reset()
        
        assert len(limiter.requests) == 0
    
    @pytest.mark.asyncio
    async def test_rate_limit_exception_includes_retry_after(self):
        """Test that 429 exception includes retry_after information."""
        limiter = RateLimiter(max_requests=1, window_seconds=30)
        request = self._create_mock_request("192.168.1.1")
        
        # Exceed limit
        await limiter.check_rate_limit(request)
        
        with pytest.raises(HTTPException) as exc_info:
            await limiter.check_rate_limit(request)
        
        assert exc_info.value.status_code == 429
        assert "retry_after" in exc_info.value.detail
        assert exc_info.value.detail["retry_after"] == 30
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_from_same_ip(self):
        """Test handling concurrent requests from same IP."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        request = self._create_mock_request("192.168.1.1")
        
        # Simulate concurrent requests
        import asyncio
        tasks = [limiter.check_rate_limit(request) for _ in range(5)]
        await asyncio.gather(*tasks)
        
        # All 5 should be recorded
        assert len(limiter.requests["192.168.1.1"]) == 5
    
    # Helper methods
    
    def _create_mock_request(self, client_ip: str, headers: dict = None) -> Request:
        """Create a mock FastAPI Request object."""
        request = Mock(spec=Request)
        
        # Mock client
        client = Mock()
        client.host = client_ip
        request.client = client
        
        # Mock headers
        request.headers = headers or {}
        
        return request


class TestRateLimiterIntegration:
    """Integration tests for RateLimiter with FastAPI."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_with_environment_variables(self, monkeypatch):
        """Test that rate limiter respects environment variables."""
        monkeypatch.setenv("RATE_LIMIT_MAX_REQUESTS", "25")
        monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "30")
        
        import os
        limiter = RateLimiter(
            max_requests=int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "100")),
            window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
        )
        
        assert limiter.max_requests == 25
        assert limiter.window == timedelta(seconds=30)
    
    @pytest.mark.asyncio
    async def test_rate_limiter_default_configuration(self):
        """Test default rate limiter configuration (100 req/60s)."""
        limiter = RateLimiter()
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.headers = {}
        
        # Should allow 100 requests
        for _ in range(100):
            await limiter.check_rate_limit(request)
        
        # 101st should fail
        with pytest.raises(HTTPException) as exc_info:
            await limiter.check_rate_limit(request)
        
        assert exc_info.value.status_code == 429


class TestRateLimiterEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.asyncio
    async def test_zero_max_requests(self):
        """Test behavior with zero max requests."""
        limiter = RateLimiter(max_requests=0, window_seconds=60)
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.headers = {}
        
        # First request should be blocked
        with pytest.raises(HTTPException):
            await limiter.check_rate_limit(request)
    
    @pytest.mark.asyncio
    async def test_very_short_window(self):
        """Test behavior with very short time window."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.headers = {}
        
        # Make 2 requests
        await limiter.check_rate_limit(request)
        await limiter.check_rate_limit(request)
        
        # Wait for window to expire
        import asyncio
        await asyncio.sleep(1.1)
        
        # Should allow new request after window expires
        await limiter.check_rate_limit(request)
        assert len(limiter.requests["192.168.1.1"]) == 1
    
    def test_get_stats_for_nonexistent_ip(self):
        """Test getting stats for IP that hasn't made requests."""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        
        stats = limiter.get_stats("192.168.1.1")
        
        assert stats["current_requests"] == 0
        assert stats["remaining"] == 10
    
    def test_reset_nonexistent_ip(self):
        """Test resetting IP that hasn't made requests."""
        limiter = RateLimiter()
        
        # Should not raise exception
        limiter.reset("192.168.1.1")
        
        assert "192.168.1.1" not in limiter.requests
