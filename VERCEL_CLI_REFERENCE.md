# Vercel CLI Command Reference

Complete reference for Vercel CLI commands used in deploying the Nova Sonic Voice-Enabled Mock Interview Coach.

## Installation

```bash
# Install globally
npm install -g vercel

# Verify installation
vercel --version

# Update to latest version
npm update -g vercel
```

## Authentication

### Login

```bash
# Login to Vercel account
vercel login

# Login with specific email
vercel login --email user@example.com

# Check current user
vercel whoami

# Logout
vercel logout
```

## Deployment Commands

### Preview Deployment

Deploy to a preview environment for testing:

```bash
# Deploy to preview (interactive)
vercel

# Deploy to preview (non-interactive)
vercel --yes

# Deploy with specific name
vercel --name my-app

# Deploy from specific directory
vercel --cwd /path/to/project

# Deploy with build environment variables
vercel --build-env NODE_ENV=production
```

**Output:**
```
Vercel CLI 28.0.0
🔍  Inspect: https://vercel.com/username/project/abc123
✅  Preview: https://project-git-branch-username.vercel.app [2s]
```

### Production Deployment

Deploy to production:

```bash
# Deploy to production
vercel --prod

# Deploy to production (non-interactive)
vercel --prod --yes

# Deploy to production with confirmation
vercel deploy --prod --confirm
```

**Output:**
```
Vercel CLI 28.0.0
🔍  Inspect: https://vercel.com/username/project/xyz789
✅  Production: https://project.vercel.app [3s]
```

### Deployment Options

```bash
# Deploy with specific scope (team)
vercel --scope team-name

# Deploy with specific token
vercel --token YOUR_TOKEN

# Deploy with debug output
vercel --debug

# Deploy without waiting for build
vercel --no-wait

# Force new deployment (skip cache)
vercel --force
```

## Environment Variables

### Add Environment Variables

```bash
# Add variable interactively
vercel env add VARIABLE_NAME

# Add to specific environment
vercel env add AWS_REGION production
vercel env add AWS_REGION preview
vercel env add AWS_REGION development

# Add to all environments
vercel env add VARIABLE_NAME production preview development

# Add from stdin
echo "value" | vercel env add VARIABLE_NAME production
```

### List Environment Variables

```bash
# List all environment variables
vercel env ls

# List for specific environment
vercel env ls production
vercel env ls preview
vercel env ls development

# List in JSON format
vercel env ls --json
```

### Remove Environment Variables

```bash
# Remove variable interactively
vercel env rm VARIABLE_NAME

# Remove from specific environment
vercel env rm VARIABLE_NAME production

# Remove from all environments
vercel env rm VARIABLE_NAME production preview development
```

### Pull Environment Variables

```bash
# Pull environment variables to .env file
vercel env pull

# Pull for specific environment
vercel env pull .env.local --environment=development
vercel env pull .env.production --environment=production
```

## Project Management

### Link Project

```bash
# Link to existing Vercel project
vercel link

# Link with specific scope
vercel link --scope team-name

# Link to specific project
vercel link --project project-name
```

### List Projects

```bash
# List all projects
vercel ls

# List projects for specific scope
vercel ls --scope team-name

# List in JSON format
vercel ls --json
```

### Project Information

```bash
# Get project information
vercel inspect

# Get deployment information
vercel inspect https://project-abc123.vercel.app
```

## Deployment Management

### List Deployments

```bash
# List all deployments
vercel ls

# List deployments for current project
vercel ls --app

# List with metadata
vercel ls --meta key=value
```

### Promote Deployment

Promote a preview deployment to production:

```bash
# Promote specific deployment
vercel promote https://project-abc123.vercel.app

# Promote with timeout
vercel promote https://project-abc123.vercel.app --timeout 60s
```

### Remove Deployment

```bash
# Remove specific deployment
vercel rm https://project-abc123.vercel.app

# Remove deployment by ID
vercel rm deployment-id

# Remove without confirmation
vercel rm deployment-id --yes
```

### Rollback

```bash
# List previous deployments
vercel ls

# Promote previous deployment to production
vercel promote https://project-previous.vercel.app
```

## Logs and Debugging

### View Logs

```bash
# View logs for latest deployment
vercel logs

# View logs for specific deployment
vercel logs https://project-abc123.vercel.app

# Follow logs in real-time
vercel logs --follow

# View logs for specific function
vercel logs --function api/websocket

# View logs with timestamp
vercel logs --since 1h
vercel logs --since 30m
vercel logs --until 2023-01-01
```

### Debug Mode

```bash
# Run any command with debug output
vercel --debug deploy
vercel --debug env ls
vercel --debug logs
```

## Local Development

### Development Server

```bash
# Start local development server
vercel dev

# Start on specific port
vercel dev --port 3000

# Start with specific environment
vercel dev --environment preview

# Start with debug output
vercel dev --debug
```

**Features:**
- ✅ HTTPS tunnel for testing microphone access
- ✅ Hot reload on file changes
- ✅ Simulates Vercel serverless environment
- ✅ Access at `https://localhost:3000`

### Build Locally

```bash
# Build project locally
vercel build

# Build for specific environment
vercel build --prod

# Build with debug output
vercel build --debug
```

## Domains

### Add Domain

```bash
# Add custom domain
vercel domains add yourdomain.com

# Add domain to specific project
vercel domains add yourdomain.com --scope team-name
```

### List Domains

```bash
# List all domains
vercel domains ls

# List domains for specific scope
vercel domains ls --scope team-name
```

### Remove Domain

```bash
# Remove domain
vercel domains rm yourdomain.com
```

## Secrets

Secrets are encrypted environment variables:

```bash
# Add secret
vercel secrets add secret-name secret-value

# List secrets
vercel secrets ls

# Remove secret
vercel secrets rm secret-name

# Rename secret
vercel secrets rename old-name new-name
```

**Using secrets in environment variables:**
```bash
# Reference secret in environment variable
vercel env add AWS_SECRET_ACCESS_KEY production
# Enter: @aws-secret-key
```

## Teams

### Switch Team

```bash
# List teams
vercel teams ls

# Switch to team
vercel switch team-name

# Deploy to team
vercel --scope team-name
```

## Aliases

### Create Alias

```bash
# Create alias for deployment
vercel alias set https://project-abc123.vercel.app yourdomain.com

# Create alias for latest deployment
vercel alias yourdomain.com
```

### List Aliases

```bash
# List all aliases
vercel alias ls

# List aliases for specific deployment
vercel alias ls https://project-abc123.vercel.app
```

### Remove Alias

```bash
# Remove alias
vercel alias rm yourdomain.com
```

## Certificates

### List Certificates

```bash
# List SSL certificates
vercel certs ls

# List certificates for specific domain
vercel certs ls yourdomain.com
```

### Issue Certificate

```bash
# Issue certificate for domain
vercel certs issue yourdomain.com

# Issue wildcard certificate
vercel certs issue *.yourdomain.com yourdomain.com
```

## Project Settings

### Get Project Settings

```bash
# Get project settings
vercel project ls

# Get specific project
vercel project ls project-name
```

### Update Project Settings

```bash
# Update project settings (via dashboard recommended)
# Or use vercel.json for configuration
```

## Common Workflows

### First-Time Deployment

```bash
# 1. Login
vercel login

# 2. Link project (if not already linked)
vercel link

# 3. Add environment variables
vercel env add AWS_REGION production
vercel env add AWS_ACCESS_KEY_ID production
vercel env add AWS_SECRET_ACCESS_KEY production
vercel env add NOVA_SONIC_MODEL_ID production

# 4. Deploy to preview
vercel

# 5. Test preview deployment
# Visit the preview URL and test all features

# 6. Deploy to production
vercel --prod
```

### Update Deployment

```bash
# 1. Make code changes
# 2. Deploy to preview for testing
vercel

# 3. Test preview deployment
# 4. Deploy to production
vercel --prod
```

### Rollback Deployment

```bash
# 1. List deployments
vercel ls

# 2. Find previous working deployment
# 3. Promote to production
vercel promote https://project-previous.vercel.app
```

### Update Environment Variables

```bash
# 1. Update variable
vercel env rm VARIABLE_NAME production
vercel env add VARIABLE_NAME production

# 2. Redeploy to apply changes
vercel --prod
```

## Troubleshooting Commands

### Check Deployment Status

```bash
# Get deployment details
vercel inspect https://project-abc123.vercel.app

# View deployment logs
vercel logs https://project-abc123.vercel.app

# Check build logs
vercel logs https://project-abc123.vercel.app --since 1h
```

### Debug Build Issues

```bash
# Build locally with debug output
vercel build --debug

# Deploy with debug output
vercel --debug

# Check function logs
vercel logs --function api/websocket
```

### Verify Configuration

```bash
# Check project link
vercel link --confirm

# List environment variables
vercel env ls

# Check project settings
vercel project ls
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Deploy to Vercel
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Vercel
        run: |
          npm install -g vercel
          vercel --token ${{ secrets.VERCEL_TOKEN }} --prod
```

### Using Vercel Token

```bash
# Deploy with token (for CI/CD)
vercel --token YOUR_VERCEL_TOKEN --prod

# Set token as environment variable
export VERCEL_TOKEN=your_token
vercel --prod
```

## Best Practices

### 1. Use Preview Deployments

Always test in preview before production:
```bash
vercel          # Test in preview
vercel --prod   # Deploy to production
```

### 2. Use Environment-Specific Variables

Configure variables for each environment:
```bash
vercel env add DEBUG development    # true
vercel env add DEBUG production     # false
```

### 3. Use Secrets for Sensitive Data

Store sensitive data as secrets:
```bash
vercel secrets add aws-secret-key "your-secret-key"
vercel env add AWS_SECRET_ACCESS_KEY production
# Enter: @aws-secret-key
```

### 4. Monitor Deployments

Check logs regularly:
```bash
vercel logs --follow
```

### 5. Keep CLI Updated

Update regularly for latest features:
```bash
npm update -g vercel
```

## Help and Documentation

### Get Help

```bash
# General help
vercel help

# Command-specific help
vercel deploy --help
vercel env --help
vercel logs --help

# List all commands
vercel --help
```

### Official Documentation

- **Vercel CLI Docs**: [vercel.com/docs/cli](https://vercel.com/docs/cli)
- **Vercel Platform Docs**: [vercel.com/docs](https://vercel.com/docs)
- **GitHub**: [github.com/vercel/vercel](https://github.com/vercel/vercel)

## Quick Reference

| Task | Command |
|------|---------|
| Login | `vercel login` |
| Deploy to preview | `vercel` |
| Deploy to production | `vercel --prod` |
| Add environment variable | `vercel env add VAR_NAME production` |
| List environment variables | `vercel env ls` |
| View logs | `vercel logs` |
| List deployments | `vercel ls` |
| Promote deployment | `vercel promote URL` |
| Start dev server | `vercel dev` |
| Get help | `vercel help` |

---

**For project-specific deployment instructions, see:**
- [DEPLOYMENT_QUICKSTART.md](./DEPLOYMENT_QUICKSTART.md) - Quick start guide
- [VERCEL_DEPLOYMENT.md](./VERCEL_DEPLOYMENT.md) - Full deployment guide
- [scripts/README.md](./scripts/README.md) - Deployment scripts documentation
