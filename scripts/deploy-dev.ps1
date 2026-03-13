# Deploy to Vercel Development/Preview Environment (PowerShell)
# This script deploys the application to a preview environment for testing

$ErrorActionPreference = "Stop"

Write-Host "🚀 Deploying to Vercel Preview Environment..." -ForegroundColor Cyan
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

# Deploy to preview
Write-Host "📦 Deploying to preview environment..." -ForegroundColor Cyan
vercel

Write-Host ""
Write-Host "✅ Preview deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Test the preview URL provided above"
Write-Host "2. Verify HTTPS is enabled (required for microphone access)"
Write-Host "3. Test WebSocket connection at /ws/{session_id}"
Write-Host "4. Check health endpoint at /api/health"
Write-Host "5. Test voice recording and playback"
Write-Host ""
Write-Host "If everything works, deploy to production with: .\scripts\deploy-prod.ps1"
