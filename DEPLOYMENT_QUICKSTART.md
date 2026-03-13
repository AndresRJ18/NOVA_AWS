# Deployment Quick Start Guide

This guide provides a streamlined path to deploy the Nova Sonic Voice-Enabled Mock Interview Coach to Vercel in under 10 minutes.

## Prerequisites Checklist

- [ ] Vercel account ([sign up free](https://vercel.com))
- [ ] AWS account with Bedrock access
- [ ] AWS credentials with Nova Sonic permissions
- [ ] Node.js installed (for Vercel CLI)

## Quick Deploy (3 Steps)

### Step 1: Install Vercel CLI

```bash
npm install -g vercel
```

### Step 2: Configure Environment Variables

**Option A: Using the setup script (Recommended)**

**Linux/Mac:**
```bash
chmod +x scripts/setup-env.sh
./scripts/setup-env.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\setup-env.ps1
```

**Option B: Manual configuration**

```bash
vercel env add AWS_REGION production
vercel env add AWS_ACCESS_KEY_ID production
vercel env add AWS_SECRET_ACCESS_KEY production
vercel env add NOVA_SONIC_MODEL_ID production
```

### Step 3: Deploy

**Preview deployment (for testing):**

**Linux/Mac:**
```bash
chmod +x scripts/deploy-dev.sh
./scripts/deploy-dev.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\deploy-dev.ps1
```

**Or manually:**
```bash
vercel
```

**Production deployment:**

**Linux/Mac:**
```bash
chmod +x scripts/deploy-prod.sh
./scripts/deploy-prod.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\deploy-prod.ps1
```

**Or manually:**
```bash
vercel --prod
```

## Verify Deployment

After deployment, test these endpoints:

1. **Health Check**: `https://your-app.vercel.app/api/health`
   - Should return `{"status": "healthy"}`

2. **Main App**: `https://your-app.vercel.app/`
   - Should load the interview coach interface

3. **Microphone Access**: Click "Start Recording"
   - Browser should request microphone permission
   - HTTPS is automatically enabled by Vercel

4. **WebSocket Connection**: Start a voice session
   - Should connect to `/ws/{session_id}`
   - Check browser console for connection status

## Common Issues & Quick Fixes

### Issue: "Vercel CLI not found"
**Fix:** Install Node.js, then run `npm install -g vercel`

### Issue: "AWS credentials invalid"
**Fix:** Verify credentials in AWS Console → IAM → Security Credentials

### Issue: "Nova Sonic unavailable"
**Fix:** 
1. Check AWS region supports Nova Sonic (us-east-1, us-west-2)
2. Verify Bedrock model access in AWS Console → Bedrock → Model access

### Issue: "Microphone permission denied"
**Fix:** Ensure you're accessing via HTTPS (automatic on Vercel)

### Issue: "WebSocket connection failed"
**Fix:** Check `vercel.json` has WebSocket route configured

## Environment Variables Reference

### Required Variables

| Variable | Example | Description |
|----------|---------|-------------|
| `AWS_REGION` | `us-east-1` | AWS region with Bedrock access |
| `AWS_ACCESS_KEY_ID` | `AKIAIOSFODNN7EXAMPLE` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` | AWS secret key |
| `NOVA_SONIC_MODEL_ID` | `amazon.nova-sonic-v1:0` | Nova Sonic model version |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AUDIO_CACHE_SIZE_MB` | `100` | Max audio cache size |
| `MAX_AUDIO_DURATION_SECONDS` | `300` | Max recording duration |
| `ENABLE_DEV_MODE` | `false` | Use mock audio (no API calls) |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## WebSocket Limitations on Vercel

⚠️ **Important Vercel WebSocket Constraints:**

- **Timeout**: 5 minutes of inactivity
  - **Solution**: Heartbeat implemented (ping/pong every 30s)
  
- **Concurrent Connections**: 10 on free tier
  - **Solution**: Upgrade to Pro plan for more connections
  
- **Max Duration**: 30 seconds per serverless function
  - **Solution**: Audio processing optimized to complete within limit

## HTTPS Requirement

Modern browsers require HTTPS for microphone access. Vercel provides this automatically:

- ✅ **Production**: `https://your-app.vercel.app`
- ✅ **Preview**: `https://your-app-git-branch.vercel.app`
- ✅ **Local Dev**: Use `vercel dev` for HTTPS tunnel

## Cost Estimation

### Free Tier Limits

**Vercel Hobby (Free):**
- 100GB bandwidth/month
- 100 hours serverless execution/month
- 10 concurrent WebSocket connections

**AWS Bedrock:**
- Pay per token (no free tier for Nova Sonic)
- ~$0.05-0.10 per interview session
- Set up budget alerts to monitor costs

### Recommended for Production

**Vercel Pro ($20/month):**
- 1TB bandwidth
- 1000 hours execution
- More concurrent connections

**AWS Budget Alert:**
- Set at $50-100/month
- Alerts at 80% and 100%

## Next Steps

After successful deployment:

1. ✅ Test voice recording and playback
2. ✅ Set up AWS budget alerts
3. ✅ Configure monitoring (see VERCEL_DEPLOYMENT.md)
4. ✅ Test on multiple browsers
5. ✅ Share preview URL with team for testing

## Need More Details?

- **Full deployment guide**: See [VERCEL_DEPLOYMENT.md](./VERCEL_DEPLOYMENT.md)
- **AWS monitoring**: See [AWS Console Monitoring](#aws-console-monitoring) in VERCEL_DEPLOYMENT.md
- **Troubleshooting**: See [Troubleshooting](#troubleshooting) section in VERCEL_DEPLOYMENT.md

## Support

- **Vercel Docs**: [vercel.com/docs](https://vercel.com/docs)
- **AWS Bedrock Docs**: [docs.aws.amazon.com/bedrock](https://docs.aws.amazon.com/bedrock)
- **Project Issues**: [GitHub Issues](https://github.com/your-repo/issues)

---

**Quick Start Complete!** 🎉

Your voice-enabled interview coach should now be live. Test it and gather feedback!
