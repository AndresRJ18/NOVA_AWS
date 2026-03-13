# Deployment Scripts

This directory contains automated deployment scripts for deploying the Nova Sonic Voice-Enabled Mock Interview Coach to Vercel.

## Available Scripts

### Environment Setup

**`setup-env.sh` / `setup-env.ps1`**
- Interactively configure Vercel environment variables
- Supports production, preview, and development environments
- Validates required variables
- Prompts for optional configuration

**Usage:**
```bash
# Linux/Mac
chmod +x setup-env.sh
./setup-env.sh

# Windows PowerShell
.\setup-env.ps1
```

### Preview Deployment

**`deploy-dev.sh` / `deploy-dev.ps1`**
- Deploy to Vercel preview environment for testing
- Creates unique preview URL
- Provides post-deployment checklist

**Usage:**
```bash
# Linux/Mac
chmod +x deploy-dev.sh
./deploy-dev.sh

# Windows PowerShell
.\deploy-dev.ps1
```

### Production Deployment

**`deploy-prod.sh` / `deploy-prod.ps1`**
- Deploy to Vercel production environment
- Requires confirmation before deploying
- Provides rollback instructions

**Usage:**
```bash
# Linux/Mac
chmod +x deploy-prod.sh
./deploy-prod.sh

# Windows PowerShell
.\deploy-prod.ps1
```

## Prerequisites

All scripts require:
- Vercel CLI installed: `npm install -g vercel`
- Vercel account (free or paid)
- AWS credentials with Bedrock access

## Deployment Workflow

### First-Time Deployment

1. **Setup environment variables:**
   ```bash
   ./scripts/setup-env.sh  # or .ps1 on Windows
   ```
   - Enter AWS credentials
   - Configure Nova Sonic model
   - Set optional parameters

2. **Deploy to preview:**
   ```bash
   ./scripts/deploy-dev.sh  # or .ps1 on Windows
   ```
   - Test the preview URL
   - Verify all features work
   - Check health endpoint

3. **Deploy to production:**
   ```bash
   ./scripts/deploy-prod.sh  # or .ps1 on Windows
   ```
   - Confirm deployment
   - Monitor health endpoint
   - Set up AWS budget alerts

### Subsequent Deployments

For updates after initial setup:

```bash
# Deploy to preview for testing
./scripts/deploy-dev.sh

# If tests pass, deploy to production
./scripts/deploy-prod.sh
```

## Script Features

### Error Handling
- ✅ Checks if Vercel CLI is installed
- ✅ Verifies user is logged in
- ✅ Validates environment selection
- ✅ Provides clear error messages

### User Experience
- ✅ Interactive prompts with defaults
- ✅ Colored output for better readability
- ✅ Post-deployment checklists
- ✅ Rollback instructions

### Security
- ✅ Secure password input for secrets
- ✅ No credentials stored in scripts
- ✅ Environment-specific configuration

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AWS_REGION` | AWS region with Bedrock | `us-east-1` |
| `AWS_ACCESS_KEY_ID` | AWS access key | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | `wJalrXUtnFEMI/K7MDENG...` |
| `NOVA_SONIC_MODEL_ID` | Nova Sonic model version | `amazon.nova-sonic-v1:0` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AUDIO_CACHE_SIZE_MB` | `100` | Max audio cache size in MB |
| `MAX_AUDIO_DURATION_SECONDS` | `300` | Max recording duration |
| `ENABLE_DEV_MODE` | `false` | Use mock audio (no API calls) |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Troubleshooting

### "Command not found: vercel"
**Solution:** Install Vercel CLI
```bash
npm install -g vercel
```

### "Permission denied" (Linux/Mac)
**Solution:** Make scripts executable
```bash
chmod +x scripts/*.sh
```

### "Execution policy" error (Windows)
**Solution:** Allow script execution
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "Not logged in to Vercel"
**Solution:** Login to Vercel
```bash
vercel login
```

### Environment variables not working
**Solution:** Verify variables are set
```bash
vercel env ls
```

## Manual Deployment

If you prefer manual deployment without scripts:

```bash
# Login
vercel login

# Set environment variables
vercel env add AWS_REGION production
vercel env add AWS_ACCESS_KEY_ID production
vercel env add AWS_SECRET_ACCESS_KEY production
vercel env add NOVA_SONIC_MODEL_ID production

# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

## Additional Resources

- **Full Deployment Guide**: [../VERCEL_DEPLOYMENT.md](../VERCEL_DEPLOYMENT.md)
- **Quick Start Guide**: [../DEPLOYMENT_QUICKSTART.md](../DEPLOYMENT_QUICKSTART.md)
- **Vercel CLI Docs**: [vercel.com/docs/cli](https://vercel.com/docs/cli)
- **AWS Bedrock Docs**: [docs.aws.amazon.com/bedrock](https://docs.aws.amazon.com/bedrock)

## Support

For issues or questions:
- Check the troubleshooting section above
- Review the full deployment guide
- Open an issue on GitHub
- Contact Vercel support for platform issues
- Contact AWS support for Bedrock issues

---

**Happy Deploying!** 🚀
