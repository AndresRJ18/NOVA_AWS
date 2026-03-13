#!/bin/bash
# Deploy to Vercel Development/Preview Environment
# This script deploys the application to a preview environment for testing

set -e  # Exit on error

echo "🚀 Deploying to Vercel Preview Environment..."
echo ""

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Error: Vercel CLI is not installed"
    echo "Install it with: npm install -g vercel"
    exit 1
fi

# Check if user is logged in
if ! vercel whoami &> /dev/null; then
    echo "🔐 Please login to Vercel..."
    vercel login
fi

# Deploy to preview
echo "📦 Deploying to preview environment..."
vercel

echo ""
echo "✅ Preview deployment complete!"
echo ""
echo "Next steps:"
echo "1. Test the preview URL provided above"
echo "2. Verify HTTPS is enabled (required for microphone access)"
echo "3. Test WebSocket connection at /ws/{session_id}"
echo "4. Check health endpoint at /api/health"
echo "5. Test voice recording and playback"
echo ""
echo "If everything works, deploy to production with: ./scripts/deploy-prod.sh"
