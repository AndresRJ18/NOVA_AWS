# Vercel Deployment Guide

This guide provides step-by-step instructions for deploying the Nova Sonic Voice-Enabled Mock Interview Coach to Vercel.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI**: Install globally
   ```bash
   npm install -g vercel
   ```
3. **AWS Credentials**: AWS account with Bedrock access and Nova Sonic permissions
4. **GitHub Repository** (recommended): For automatic deployments

## Project Structure

```
project-root/
├── api/                          # Vercel serverless functions
│   ├── __init__.py
│   ├── websocket.py             # WebSocket handler
│   └── health.py                # Health check endpoint
├── mock_interview_coach/        # Application code
├── static/                      # Frontend files
│   ├── index.html
│   ├── js/
│   └── css/
├── vercel.json                  # Vercel configuration
├── requirements.txt             # Python dependencies
└── .env.example                 # Environment variables template
```

## Configuration Files

### vercel.json

The `vercel.json` file configures:
- **Builds**: Python serverless functions and static files
- **Routes**: URL routing for API, WebSocket, and static content
- **Environment Variables**: AWS credentials and configuration
- **Functions**: Memory (1024MB) and max duration (30s)

### Environment Variables

Required variables:
- `AWS_REGION`: AWS region for Bedrock (e.g., "us-east-1")
- `AWS_ACCESS_KEY_ID`: AWS access key with Bedrock permissions
- `AWS_SECRET_ACCESS_KEY`: AWS secret access key
- `NOVA_SONIC_MODEL_ID`: Model ID (default: "amazon.nova-sonic-v1:0")

Optional variables:
- `AUDIO_CACHE_SIZE_MB`: Max cache size in MB (default: 100)
- `MAX_AUDIO_DURATION_SECONDS`: Max recording duration (default: 300)
- `ENABLE_DEV_MODE`: Use mock audio instead of API (default: false)
- `LOG_LEVEL`: Logging level (default: "INFO")

## Deployment Steps

### Using Deployment Scripts (Recommended)

The project includes automated deployment scripts for easier deployment:

**Linux/Mac:**
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Setup environment variables
./scripts/setup-env.sh

# Deploy to preview
./scripts/deploy-dev.sh

# Deploy to production
./scripts/deploy-prod.sh
```

**Windows (PowerShell):**
```powershell
# Setup environment variables
.\scripts\setup-env.ps1

# Deploy to preview
.\scripts\deploy-dev.ps1

# Deploy to production
.\scripts\deploy-prod.ps1
```

**What the scripts do:**
- ✅ Check if Vercel CLI is installed
- ✅ Verify user is logged in
- ✅ Configure environment variables interactively
- ✅ Deploy with proper settings
- ✅ Provide post-deployment checklist

### Option 1: Deploy via Vercel CLI (Manual)

#### 1. Login to Vercel

```bash
vercel login
```

#### 2. Set Environment Variables

You can set environment variables via CLI:

```bash
# Production environment
vercel env add AWS_REGION production
# Enter value: us-east-1

vercel env add AWS_ACCESS_KEY_ID production
# Enter value: your_access_key

vercel env add AWS_SECRET_ACCESS_KEY production
# Enter value: your_secret_key

vercel env add NOVA_SONIC_MODEL_ID production
# Enter value: amazon.nova-sonic-v1:0
```

Or via Vercel Dashboard:
1. Go to your project settings
2. Navigate to "Environment Variables"
3. Add each variable for Production, Preview, and Development environments

#### 3. Deploy to Preview (Testing)

```bash
# Deploy to preview environment
vercel
```

This creates a preview deployment with a unique URL like:
`https://your-app-git-branch.vercel.app`

#### 4. Test Preview Deployment

- Verify HTTPS is enabled (required for microphone access)
- Test WebSocket connection at `/ws/{session_id}`
- Check health endpoint at `/api/health`
- Test voice recording and playback

#### 5. Deploy to Production

```bash
# Deploy to production
vercel --prod
```

Production URL: `https://your-app.vercel.app`

### Option 2: Deploy via GitHub Integration (Recommended)

#### 1. Connect GitHub Repository

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repository
3. Configure project settings:
   - Framework Preset: Other
   - Root Directory: ./
   - Build Command: (leave empty)
   - Output Directory: static

#### 2. Configure Environment Variables

In Vercel Dashboard:
1. Go to Project Settings → Environment Variables
2. Add all required variables (see list above)
3. Set variables for all environments (Production, Preview, Development)

#### 3. Deploy

- **Automatic**: Push to `main` branch → automatic production deployment
- **Preview**: Push to any other branch → automatic preview deployment

## WebSocket Configuration

### Vercel WebSocket Support

Vercel supports WebSockets through serverless functions with these limitations:

- **Timeout**: 5 minutes of inactivity
  - After 5 minutes without messages, connection is automatically closed
  - **Mitigation**: Heartbeat ping/pong every 30 seconds (implemented)
  
- **Concurrent Connections**: 10 on free tier, more on paid plans
  - Free (Hobby): 10 concurrent connections
  - Pro: 100 concurrent connections
  - Enterprise: Custom limits
  - **Recommendation**: Upgrade to Pro for production use
  
- **Protocol**: WSS (WebSocket Secure) over HTTPS
  - Only secure WebSocket connections (wss://) are supported
  - HTTP WebSocket (ws://) will fail
  
- **Function Duration**: 30 seconds max per serverless function invocation
  - Audio processing must complete within this limit
  - **Mitigation**: Optimized audio processing pipeline

### Heartbeat Implementation

The WebSocket handler implements ping/pong heartbeat to keep connections alive:

```python
# Server sends heartbeat every 30 seconds to prevent timeout
await websocket.send_json({"type": "ping"})
```

Client should respond with pong:

```javascript
websocket.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === 'ping') {
    websocket.send(JSON.stringify({ type: 'pong' }));
  }
};
```

### WebSocket Connection Best Practices

1. **Implement Reconnection Logic**: Handle disconnections gracefully
   ```javascript
   let reconnectAttempts = 0;
   const maxReconnectAttempts = 3;
   
   function connectWebSocket() {
     const ws = new WebSocket('wss://your-app.vercel.app/ws/session-id');
     
     ws.onclose = () => {
       if (reconnectAttempts < maxReconnectAttempts) {
         reconnectAttempts++;
         setTimeout(connectWebSocket, 1000 * reconnectAttempts);
       } else {
         // Fallback to text mode
         switchToTextMode();
       }
     };
   }
   ```

2. **Monitor Connection Health**: Track connection state
   ```javascript
   let lastPingTime = Date.now();
   
   ws.onmessage = (event) => {
     const message = JSON.parse(event.data);
     if (message.type === 'ping') {
       lastPingTime = Date.now();
       ws.send(JSON.stringify({ type: 'pong' }));
     }
   };
   
   // Check if connection is stale
   setInterval(() => {
     if (Date.now() - lastPingTime > 60000) {
       console.warn('Connection may be stale, reconnecting...');
       ws.close();
     }
   }, 10000);
   ```

3. **Handle Errors Gracefully**: Provide fallback options
   ```javascript
   ws.onerror = (error) => {
     console.error('WebSocket error:', error);
     showErrorMessage('Connection error. Switching to text mode.');
     switchToTextMode();
   };
   ```

## HTTPS and Microphone Access

### Why HTTPS is Required

Modern browsers require HTTPS for microphone access due to security policies:

- **Chrome/Edge**: Requires HTTPS for `getUserMedia()` API
- **Firefox**: Requires HTTPS for microphone access
- **Safari**: Requires HTTPS for media device access
- **Exception**: `localhost` is treated as secure context (for local development)

**Security Rationale:**
- Prevents malicious sites from accessing microphone without user knowledge
- Ensures encrypted transmission of audio data
- Protects user privacy

**What Happens Without HTTPS:**
```javascript
// This will fail on HTTP (except localhost)
navigator.mediaDevices.getUserMedia({ audio: true })
  .catch(error => {
    // Error: "Only secure origins are allowed"
    console.error(error);
  });
```

### Vercel HTTPS Configuration

Vercel automatically provides HTTPS for all deployments:

- ✅ **Production**: `https://your-app.vercel.app`
  - Automatic SSL certificate from Let's Encrypt
  - Auto-renewal every 90 days
  - No configuration required

- ✅ **Preview**: `https://your-app-git-branch.vercel.app`
  - Each preview deployment gets unique HTTPS URL
  - Useful for testing before production

- ✅ **Custom Domain**: `https://yourdomain.com`
  - Add custom domain in Vercel dashboard
  - Automatic SSL certificate provisioning
  - DNS configuration required

### Local Development with HTTPS

For local testing with microphone:

**Option 1: Vercel Dev Environment (Recommended)**
```bash
vercel dev
```
- Provides local HTTPS tunnel
- Automatically handles SSL certificates
- Mirrors production environment
- Access at: `https://localhost:3000`

**Option 2: ngrok**
```bash
# Install ngrok
npm install -g ngrok

# Run your local server
python run.py

# Create HTTPS tunnel
ngrok http 5000
```
- Provides public HTTPS URL
- Useful for testing on mobile devices
- Free tier available
- Example URL: `https://abc123.ngrok.io`

**Option 3: Self-Signed Certificate**
```bash
# Generate certificate
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Run Flask with HTTPS
python run.py --ssl
```
- Access at: `https://localhost:5000`
- Browser will show security warning
- Click "Advanced" → "Proceed to localhost (unsafe)"
- **Note**: Self-signed certificates require browser security exception

**Option 4: mkcert (Local CA)**
```bash
# Install mkcert
brew install mkcert  # macOS
choco install mkcert  # Windows

# Create local CA
mkcert -install

# Generate certificate for localhost
mkcert localhost 127.0.0.1 ::1

# Use generated cert.pem and key.pem with your server
```
- No browser warnings
- Trusted by system
- Best for frequent local development

### Testing Microphone Access

After deploying to HTTPS, test microphone access:

1. **Open Browser Console** (F12)
2. **Navigate to your app**
3. **Click "Start Recording"**
4. **Check for permission prompt**:
   ```
   ✅ Good: Browser shows "Allow microphone access?"
   ❌ Bad: Console error "Only secure origins are allowed"
   ```

5. **Grant permission and verify**:
   ```javascript
   // Check if permission granted
   navigator.permissions.query({ name: 'microphone' })
     .then(result => {
       console.log('Microphone permission:', result.state);
       // "granted", "denied", or "prompt"
     });
   ```

### Troubleshooting HTTPS Issues

**Issue**: "Not secure" warning in browser
- **Cause**: Accessing via HTTP instead of HTTPS
- **Fix**: Ensure URL starts with `https://`

**Issue**: "NET::ERR_CERT_AUTHORITY_INVALID" on localhost
- **Cause**: Self-signed certificate not trusted
- **Fix**: Click "Advanced" → "Proceed" or use mkcert

**Issue**: Microphone works on localhost but not on deployment
- **Cause**: Deployment not using HTTPS
- **Fix**: Verify Vercel deployment URL starts with `https://`

**Issue**: Mixed content warning
- **Cause**: Loading HTTP resources on HTTPS page
- **Fix**: Ensure all resources (scripts, styles, WebSocket) use HTTPS/WSS

### Security Best Practices

1. **Always use HTTPS in production**
   - Never deploy voice features over HTTP
   - Vercel handles this automatically

2. **Use WSS for WebSocket connections**
   ```javascript
   // Good
   const ws = new WebSocket('wss://your-app.vercel.app/ws/session');
   
   // Bad (will fail on HTTPS page)
   const ws = new WebSocket('ws://your-app.vercel.app/ws/session');
   ```

3. **Validate SSL certificates**
   - Don't disable certificate validation in production
   - Use proper certificates from trusted CA

4. **Handle permission denials gracefully**
   ```javascript
   navigator.mediaDevices.getUserMedia({ audio: true })
     .then(stream => {
       // Microphone access granted
       startRecording(stream);
     })
     .catch(error => {
       if (error.name === 'NotAllowedError') {
         showMessage('Microphone permission denied. Please enable in browser settings.');
       } else if (error.name === 'NotSecureError') {
         showMessage('HTTPS required for microphone access.');
       }
       // Fallback to text mode
       switchToTextMode();
     });
   ```

## Health Monitoring

### Health Check Endpoint

The `/api/health` endpoint provides system status:

```bash
curl https://your-app.vercel.app/api/health
```

Response:
```json
{
  "status": "healthy",
  "mode": "production",
  "nova_sonic": "available",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

Status values:
- `healthy`: All systems operational
- `degraded`: Nova Sonic unavailable (text mode still works)
- `unhealthy`: Critical error (503 status code)

### Setting Up Monitoring

**Option 1: Vercel Analytics**
- Automatically enabled for all deployments
- View in Vercel Dashboard → Analytics

**Option 2: External Monitoring**
- Use UptimeRobot, Pingdom, or similar
- Monitor `/api/health` endpoint
- Alert on 503 status or "unhealthy" status

**Option 3: AWS CloudWatch**
- Monitor Bedrock API metrics
- Set up alarms for high error rates
- Track token usage and costs

## Rate Limiting

The deployment includes rate limiting to prevent abuse:

- **Default**: 100 requests per 60 seconds per IP
- **Response**: 429 status code when exceeded
- **Configuration**: Modify in `api/websocket.py`

## Rollback Strategy

### Via Vercel Dashboard

1. Go to Deployments tab
2. Find previous working deployment
3. Click "Promote to Production"

### Via Vercel CLI

```bash
# List deployments
vercel ls

# Promote specific deployment
vercel promote <deployment-url>
```

### Automated Rollback

Set up health check monitoring to trigger automatic rollback:

1. Monitor `/api/health` endpoint
2. If status is "unhealthy" for >5 minutes
3. Use Vercel API to rollback to previous deployment

## AWS Console Monitoring

### Accessing Bedrock Metrics

1. Log in to [AWS Console](https://console.aws.amazon.com)
2. Navigate to Amazon Bedrock service
3. Click "Monitoring" in left sidebar
4. Select "Usage metrics"
5. Filter by model: `amazon.nova-sonic-v1:0`

### Key Metrics

- **Invocations**: Total API calls per time period
- **Input tokens**: Audio input processed
- **Output tokens**: Audio/text generated
- **Errors**: Failed API calls
- **Throttles**: Rate limit hits

### Setting Up Cost Alerts

1. Navigate to AWS Billing Dashboard
2. Click "Budgets" in left sidebar
3. Create new budget:
   - Budget type: Cost budget
   - Period: Monthly
   - Amount: Your threshold (e.g., $100)
   - Filters: Service = Amazon Bedrock
4. Configure alerts:
   - Alert at 80% of budget
   - Alert at 100% of budget
   - Email notifications to admin

### Useful AWS Links

- [AWS Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [AWS Bedrock Monitoring Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/monitoring.html)
- [AWS Cost Management](https://aws.amazon.com/aws-cost-management/)

## Development Mode

For testing without consuming AWS credits:

1. Set environment variable:
   ```bash
   vercel env add ENABLE_DEV_MODE development
   # Enter value: true
   ```

2. Deploy to preview:
   ```bash
   vercel
   ```

3. Dev mode uses mock audio files instead of Nova Sonic API

## Troubleshooting

### Common Issues

**Issue**: Microphone permission denied
- **Solution**: Ensure deployment uses HTTPS (automatic on Vercel)

**Issue**: WebSocket connection fails
- **Solution**: Check that route `/ws/{session_id}` is configured in `vercel.json`

**Issue**: Nova Sonic unavailable
- **Solution**: Verify AWS credentials and region in environment variables

**Issue**: Function timeout (30s limit)
- **Solution**: Optimize audio processing or increase timeout in `vercel.json`

**Issue**: High latency
- **Solution**: Check AWS region (use closest to users), enable audio caching

### Logs and Debugging

View logs in Vercel Dashboard:
1. Go to your project
2. Click on a deployment
3. Navigate to "Functions" tab
4. Click on a function to view logs

Or via CLI:
```bash
vercel logs <deployment-url>
```

## Performance Optimization

### Audio Caching

The system caches common audio responses to reduce API calls:

- Cache size: 100MB (configurable via `AUDIO_CACHE_SIZE_MB`)
- Cache hit rate: 60%+ for common phrases
- TTL: 24 hours for common phrases, 1 hour for dynamic content

### Latency Targets

- Speech-to-text: <2 seconds (p95)
- Text-to-speech: <3 seconds (p95)
- End-to-end: <5 seconds (p95)
- WebSocket transmission: <500ms (p95)

### Bandwidth Optimization

- Audio compression: 64kbps MP3, 48kbps Opus
- Streaming playback: Start before complete audio generated
- Binary WebSocket frames: Efficient audio transmission

## Security Best Practices

1. **Never commit credentials**: Use environment variables
2. **Rotate AWS keys**: Regularly update access keys
3. **Minimum permissions**: Grant only Bedrock invoke permissions
4. **Rate limiting**: Prevent abuse and excessive costs
5. **Input validation**: Validate all audio and text inputs
6. **HTTPS only**: Ensure all traffic is encrypted

## Cost Estimation

### Nova Sonic Pricing (as of 2024)

- Input: ~$0.003 per 1000 tokens
- Output: ~$0.012 per 1000 tokens
- Average session: ~$0.05-0.10

### Vercel Pricing

- **Hobby (Free)**: 100GB bandwidth, 100 hours serverless execution
- **Pro ($20/month)**: 1TB bandwidth, 1000 hours execution
- **Enterprise**: Custom pricing

### Cost Optimization Tips

1. Enable audio caching (reduces API calls by 60%)
2. Use development mode for testing
3. Set up AWS budget alerts
4. Monitor usage via AWS Console
5. Optimize audio compression

## Next Steps

After successful deployment:

1. ✅ Test all voice features in production
2. ✅ Set up health monitoring
3. ✅ Configure AWS budget alerts
4. ✅ Test on multiple browsers and devices
5. ✅ Monitor latency and error rates
6. ✅ Gather user feedback
7. ✅ Optimize based on usage patterns

## Support

For issues or questions:

- **Vercel Documentation**: [vercel.com/docs](https://vercel.com/docs)
- **Vercel CLI Reference**: [VERCEL_CLI_REFERENCE.md](./VERCEL_CLI_REFERENCE.md) - Complete CLI command reference
- **Quick Start Guide**: [DEPLOYMENT_QUICKSTART.md](./DEPLOYMENT_QUICKSTART.md) - Fast deployment guide
- **Deployment Scripts**: [scripts/README.md](./scripts/README.md) - Automated deployment scripts
- **AWS Bedrock Documentation**: [docs.aws.amazon.com/bedrock](https://docs.aws.amazon.com/bedrock)
- **Project Issues**: [GitHub Issues](https://github.com/your-repo/issues)

---

**Requirements Validated**: 12.1, 12.4, 13.1, 13.2

## Deployment Scripts

The project includes automated deployment scripts in the `scripts/` directory:

- **`setup-env.sh` / `setup-env.ps1`**: Interactive environment variable configuration
- **`deploy-dev.sh` / `deploy-dev.ps1`**: Deploy to preview environment
- **`deploy-prod.sh` / `deploy-prod.ps1`**: Deploy to production environment

See [scripts/README.md](scripts/README.md) for detailed usage instructions.

### Quick Deploy

**Linux/Mac:**
```bash
chmod +x scripts/*.sh
./scripts/setup-env.sh
./scripts/deploy-dev.sh
```

**Windows:**
```powershell
.\scripts\setup-env.ps1
.\scripts\deploy-dev.ps1
```

For a complete quick start guide, see [DEPLOYMENT_QUICKSTART.md](DEPLOYMENT_QUICKSTART.md).
