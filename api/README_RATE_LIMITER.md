# Rate Limiting Middleware

## Overview

The rate limiting middleware protects the Nova Sonic Voice Integration API from abuse and excessive usage by tracking requests per client IP address and enforcing configurable limits.

**Requirements:** 13.4

## Features

- **Per-IP Tracking**: Tracks requests independently for each client IP address
- **Configurable Limits**: Customizable maximum requests and time window
- **Automatic Cleanup**: Removes expired request records outside the time window
- **429 Status Code**: Returns standard HTTP 429 (Too Many Requests) when limit exceeded
- **Vercel Compatible**: Handles X-Forwarded-For header for proxied requests
- **Statistics API**: Provides rate limiter statistics for monitoring

## Configuration

### Environment Variables

Configure rate limiting via environment variables:

```bash
# Maximum requests per IP within time window (default: 100)
RATE_LIMIT_MAX_REQUESTS=100

# Time window in seconds (default: 60)
RATE_LIMIT_WINDOW_SECONDS=60
```

### Default Configuration

If environment variables are not set, the rate limiter uses these defaults:
- **Max Requests**: 100 requests
- **Time Window**: 60 seconds (1 minute)

This allows 100 requests per minute per IP address.

## Usage

### Automatic Integration

The rate limiter is automatically integrated into all API endpoints via FastAPI middleware:

```python
from api.rate_limiter import RateLimiter

# Initialize rate limiter
rate_limiter = RateLimiter(
    max_requests=int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "100")),
    window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
)

# Apply as middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    await rate_limiter.check_rate_limit(request)
    response = await call_next(request)
    return response
```

### Manual Usage

You can also use the rate limiter directly in specific endpoints:

```python
from api.rate_limiter import RateLimiter

rate_limiter = RateLimiter(max_requests=50, window_seconds=30)

@app.get("/api/my-endpoint")
async def my_endpoint(request: Request):
    # Check rate limit
    await rate_limiter.check_rate_limit(request)
    
    # Your endpoint logic here
    return {"status": "ok"}
```

## API Reference

### RateLimiter Class

#### Constructor

```python
RateLimiter(max_requests: int = 100, window_seconds: int = 60)
```

**Parameters:**
- `max_requests`: Maximum number of requests allowed per IP within the time window
- `window_seconds`: Time window in seconds for rate limiting

#### Methods

##### check_rate_limit(request: Request) -> None

Check if the request exceeds the rate limit.

**Parameters:**
- `request`: FastAPI Request object

**Raises:**
- `HTTPException`: 429 status code if rate limit exceeded

**Example:**
```python
await rate_limiter.check_rate_limit(request)
```

##### get_stats(client_ip: str = None) -> dict

Get rate limiter statistics.

**Parameters:**
- `client_ip`: Optional IP address to get stats for specific client

**Returns:**
- Dictionary with rate limiter statistics

**Example:**
```python
# Get stats for specific IP
stats = rate_limiter.get_stats("192.168.1.1")
# Returns: {
#   "client_ip": "192.168.1.1",
#   "current_requests": 45,
#   "max_requests": 100,
#   "window_seconds": 60,
#   "remaining": 55
# }

# Get overall stats
stats = rate_limiter.get_stats()
# Returns: {
#   "total_tracked_ips": 10,
#   "max_requests": 100,
#   "window_seconds": 60
# }
```

##### reset(client_ip: str = None) -> None

Reset rate limiter for a specific IP or all IPs.

**Parameters:**
- `client_ip`: Optional IP address to reset. If None, resets all IPs.

**Example:**
```python
# Reset specific IP
rate_limiter.reset("192.168.1.1")

# Reset all IPs
rate_limiter.reset()
```

## Error Response

When rate limit is exceeded, the API returns a 429 status code with this response:

```json
{
  "error": "Rate limit exceeded",
  "message": "Maximum 100 requests per 60 seconds allowed",
  "retry_after": 60
}
```

**Fields:**
- `error`: Error type identifier
- `message`: Human-readable error message
- `retry_after`: Seconds to wait before retrying

## Client IP Detection

The rate limiter extracts the client IP address using this priority:

1. **X-Forwarded-For header** (for Vercel/proxy deployments)
   - Takes the first IP in the chain
   - Example: `X-Forwarded-For: 203.0.113.1, 198.51.100.1` → `203.0.113.1`

2. **Direct connection** (for local development)
   - Uses `request.client.host`

3. **Fallback** (if no client info available)
   - Uses `"unknown"` as IP address

## Monitoring

### Check Rate Limiter Status

You can monitor rate limiter statistics by calling `get_stats()`:

```python
# Get stats for specific IP
stats = rate_limiter.get_stats("203.0.113.1")
print(f"IP {stats['client_ip']} has {stats['remaining']} requests remaining")

# Get overall stats
stats = rate_limiter.get_stats()
print(f"Tracking {stats['total_tracked_ips']} unique IPs")
```

### Logging

The rate limiter logs important events:

```
[INFO] RateLimiter initialized: max_requests=100, window_seconds=60
[DEBUG] Rate limit check passed: client_ip=203.0.113.1, requests=45/100
[WARN] Rate limit exceeded: client_ip=203.0.113.1, requests=100, max=100
[INFO] Rate limiter reset for client_ip=203.0.113.1
```

## Testing

Run the comprehensive test suite:

```bash
# Run all rate limiter tests
python -m pytest tests/test_rate_limiter.py -v

# Run specific test class
python -m pytest tests/test_rate_limiter.py::TestRateLimiter -v

# Run with coverage
python -m pytest tests/test_rate_limiter.py --cov=api.rate_limiter
```

## Deployment Considerations

### Vercel Serverless Functions

When deployed to Vercel, each serverless function instance has its own rate limiter state. This means:

- Rate limits are enforced per function instance
- Multiple instances may have different request counts for the same IP
- For stricter rate limiting, consider using a shared state store (Redis, DynamoDB)

### Memory Usage

The rate limiter stores request timestamps in memory:

- Each IP address: ~100 bytes
- Each timestamp: ~24 bytes
- Example: 1000 IPs × 100 requests = ~2.4 MB

Memory usage is automatically managed by cleaning expired requests.

### Production Recommendations

For production deployments:

1. **Set appropriate limits**: Balance between user experience and abuse prevention
   - API endpoints: 100 requests/minute
   - WebSocket connections: 10 connections/minute
   - Health checks: 1000 requests/minute (higher limit)

2. **Monitor rate limit hits**: Track 429 responses to identify legitimate users hitting limits

3. **Consider IP whitelisting**: Allow higher limits for trusted IPs (admin, monitoring)

4. **Use shared state**: For multi-instance deployments, use Redis or similar for shared rate limiting

## Examples

### Different Limits for Different Endpoints

```python
# Strict rate limiting for expensive operations
strict_limiter = RateLimiter(max_requests=10, window_seconds=60)

# Lenient rate limiting for health checks
lenient_limiter = RateLimiter(max_requests=1000, window_seconds=60)

@app.get("/api/expensive-operation")
async def expensive_operation(request: Request):
    await strict_limiter.check_rate_limit(request)
    # ... expensive operation

@app.get("/api/health")
async def health_check(request: Request):
    await lenient_limiter.check_rate_limit(request)
    # ... health check
```

### Custom Error Handling

```python
from fastapi import HTTPException, Request
from api.rate_limiter import RateLimiter

rate_limiter = RateLimiter()

@app.get("/api/my-endpoint")
async def my_endpoint(request: Request):
    try:
        await rate_limiter.check_rate_limit(request)
    except HTTPException as e:
        if e.status_code == 429:
            # Custom handling for rate limit exceeded
            return {
                "error": "Too many requests",
                "message": "Please slow down and try again later",
                "retry_after": e.detail["retry_after"]
            }
        raise
    
    # Your endpoint logic here
    return {"status": "ok"}
```

## Troubleshooting

### Issue: Rate limit too strict

**Symptoms:** Legitimate users getting 429 errors

**Solution:** Increase `RATE_LIMIT_MAX_REQUESTS` or `RATE_LIMIT_WINDOW_SECONDS`

```bash
# Allow 200 requests per minute instead of 100
RATE_LIMIT_MAX_REQUESTS=200
```

### Issue: Rate limit too lenient

**Symptoms:** Abuse or excessive API usage

**Solution:** Decrease `RATE_LIMIT_MAX_REQUESTS` or `RATE_LIMIT_WINDOW_SECONDS`

```bash
# Allow only 50 requests per minute
RATE_LIMIT_MAX_REQUESTS=50
```

### Issue: Rate limiter not working

**Symptoms:** No 429 errors even with excessive requests

**Solution:** Verify middleware is applied correctly

```python
# Check that middleware is registered
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    await rate_limiter.check_rate_limit(request)
    response = await call_next(request)
    return response
```

### Issue: All requests from same IP

**Symptoms:** All requests appear to come from same IP address

**Solution:** Verify X-Forwarded-For header is being passed by proxy

```python
# Debug IP detection
ip = rate_limiter._get_client_ip(request)
print(f"Detected IP: {ip}")
print(f"X-Forwarded-For: {request.headers.get('X-Forwarded-For')}")
print(f"Client host: {request.client.host if request.client else 'None'}")
```

## Security Considerations

1. **IP Spoofing**: The rate limiter trusts the X-Forwarded-For header. Ensure your proxy (Vercel) is configured to set this correctly.

2. **Memory Exhaustion**: The rate limiter stores data in memory. For very high traffic, consider using a distributed cache.

3. **Bypass via Multiple IPs**: Attackers with multiple IP addresses can bypass rate limiting. Consider additional security measures (authentication, CAPTCHA).

4. **DDoS Protection**: Rate limiting helps but is not a complete DDoS solution. Use Vercel's built-in DDoS protection and consider additional services (Cloudflare).

## License

This rate limiting middleware is part of the Nova Sonic Voice Integration project.
