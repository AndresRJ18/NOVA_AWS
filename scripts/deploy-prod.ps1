# Deploy to Vercel Production Environment (PowerShell)
# This script deploys the application to production

$ErrorActionPreference = "Stop"

Write-Host "🚀 Deploying to Vercel Production Environment..." -ForegroundColor Cyan
Write-Host ""

# Check if Vercel CLI is installed
try {
    vercel --version | Out-Null
} catch {
    Write-Host "❌ Error: Vercel CLI is not installed" -ForegroundColor Red
    Write-Host "Install it with: npm install -g vercel"
    exit 1
}

# Check if user is logged in
try {
    vercel whoami | Out-Null
} catch {
    Write-Host "🔐 Please login to Vercel..." -ForegroundColor Yellow
    vercel login
}

# Confirm production deployment
Write-Host "⚠️  WARNING: This will deploy to PRODUCTION" -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "Are you sure you want to continue? (yes/no)"

if ($confirm -ne "yes") {
    Write-Host "❌ Deployment cancelled" -ForegroundColor Red
    exit 0
}

# Deploy to production
Write-Host "📦 Deploying to production environment..." -ForegroundColor Cyan
vercel --prod

Write-Host ""
Write-Host "✅ Production deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Test the production URL"
Write-Host "2. Monitor health endpoint: /api/health"
Write-Host "3. Check AWS Console for Bedrock usage"
Write-Host "4. Set up monitoring alerts"
Write-Host "5. Monitor error rates and latency"
Write-Host ""
Write-Host "To rollback if needed: vercel promote <previous-deployment-url>"
