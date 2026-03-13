# Vercel Environment Variables Setup

Quick reference guide for setting up environment variables in Vercel.

## Required Environment Variables

### AWS Credentials

```bash
# AWS Region (where Bedrock is available)
vercel env add AWS_REGION
# Value: us-east-1 (or your preferred region)

# AWS Access Key ID
vercel env add AWS_ACCESS_KEY_ID
# Value: Your AWS access key with Bedrock permissions

# AWS Secret Access Key
vercel env add AWS_SECRET_ACCESS_KEY
# Value: Your AWS secret key
```

### Nova Sonic Configuration

```bash
# Nova Sonic Model ID
vercel env add NOVA_SONIC_MODEL_ID
# Value: amazon.nova-sonic-v1:0 (or amazon.nova-2-sonic-v1:0)
```

## Optional Environment Variables

```bash
# Audio cache size in MB (default: 100)
vercel env add AUDIO_CACHE_SIZE_MB
# Value: 100

# Maximum audio duration in seconds (default: 300)
vercel env add MAX_AUDIO_DURATION_SECONDS
# Value: 300

# Enable development mode with mock audio (default: false)
vercel env add ENABLE_DEV_MODE
# Value: false

# Logging level (default: INFO)
vercel env add LOG_LEVEL
# Value: INFO
```

## Setting Variables for Different Environments

When prompted, select which environments to add the variable to:

- **Production**: Live deployment at your-app.vercel.app
- **Preview**: Branch deployments for testing
- **Development**: Local development with `vercel dev`

### Example Session

```bash
$ vercel env add AWS_REGION
? What's the value of AWS_REGION? us-east-1
? Add AWS_REGION to which Environments (select multiple)?
  ◉ Production
  ◉ Preview
  ◉ Development
✓ Added Environment Variable AWS_REGION to Project nova-sonic-voice
```

## Via Vercel Dashboard

Alternatively, set variables via the web interface:

1. Go to [vercel.com](https://vercel.com)
2. Select your project
3. Navigate to **Settings** → **Environment Variables**
4. Click **Add New**
5. Enter:
   - **Key**: Variable name (e.g., AWS_REGION)
   - **Value**: Variable value (e.g., us-east-1)
   - **Environments**: Select Production, Preview, Development
6. Click **Save**

## Verifying Environment Variables

### List All Variables

```bash
vercel env ls
```

### Pull Variables to Local .env

```bash
vercel env pull .env.local
```

This creates a `.env.local` file with all environment variables for local development.

## Security Best Practices

1. **Never commit credentials**: Keep `.env` files in `.gitignore`
2. **Use Vercel Secrets**: For sensitive values, use `@secret-name` syntax in `vercel.json`
3. **Rotate keys regularly**: Update AWS credentials periodically
4. **Minimum permissions**: Grant only Bedrock invoke permissions to AWS keys
5. **Separate environments**: Use different AWS keys for production vs development

## AWS IAM Permissions

Your AWS access key needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/amazon.nova-sonic-v1:0",
        "arn:aws:bedrock:*::foundation-model/amazon.nova-2-sonic-v1:0"
      ]
    }
  ]
}
```

## Troubleshooting

### Variable Not Found

If deployment fails with "environment variable not found":

1. Verify variable is set: `vercel env ls`
2. Check variable name matches exactly (case-sensitive)
3. Ensure variable is set for correct environment (Production/Preview/Development)
4. Redeploy: `vercel --prod`

### AWS Credentials Invalid

If health check shows "Nova Sonic unavailable":

1. Verify AWS credentials are correct
2. Check AWS region supports Bedrock Nova Sonic
3. Verify IAM permissions include `bedrock:InvokeModel`
4. Test credentials locally with `check_nova_access.py`

### Development Mode Not Working

If dev mode doesn't use mock audio:

1. Verify `ENABLE_DEV_MODE=true` is set
2. Check environment is set to Development
3. Redeploy: `vercel`

## Quick Setup Script

Copy and paste this script to set all required variables at once:

```bash
#!/bin/bash

# Required variables
vercel env add AWS_REGION production preview development
vercel env add AWS_ACCESS_KEY_ID production preview development
vercel env add AWS_SECRET_ACCESS_KEY production preview development
vercel env add NOVA_SONIC_MODEL_ID production preview development

# Optional variables with defaults
echo "100" | vercel env add AUDIO_CACHE_SIZE_MB production preview development
echo "300" | vercel env add MAX_AUDIO_DURATION_SECONDS production preview development
echo "false" | vercel env add ENABLE_DEV_MODE production preview
echo "true" | vercel env add ENABLE_DEV_MODE development
echo "INFO" | vercel env add LOG_LEVEL production preview development
```

Save as `setup-vercel-env.sh`, make executable, and run:

```bash
chmod +x setup-vercel-env.sh
./setup-vercel-env.sh
```

---

**Requirements Validated**: 12.1
