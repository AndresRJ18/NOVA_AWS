#!/bin/bash
# Deploy to Vercel Production Environment
# This script deploys the application to production

set -e  # Exit on error

echo "🚀 Deploying to Vercel Production Environment..."
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

# Confirm production deployment
echo "⚠️  WARNING: This will deploy to PRODUCTION"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Deployment cancelled"
    exit 0
fi

# Deploy to production
echo "📦 Deploying to production environment..."
vercel --prod

echo ""
echo "✅ Production deployment complete!"
echo ""
echo "Next steps:"
echo "1. Test the production URL"
echo "2. Monitor health endpoint: /api/health"
echo "3. Check AWS Console for Bedrock usage"
echo "4. Set up monitoring alerts"
echo "5. Monitor error rates and latency"
echo ""
echo "To rollback if needed: vercel promote <previous-deployment-url>"
