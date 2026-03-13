#!/bin/bash
# Setup Environment Variables for Vercel
# This script helps configure environment variables via Vercel CLI

set -e  # Exit on error

echo "🔧 Setting up Vercel Environment Variables..."
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

# Select environment
echo "Select environment to configure:"
echo "1) Production"
echo "2) Preview"
echo "3) Development"
echo "4) All environments"
read -p "Enter choice (1-4): " env_choice

case $env_choice in
    1) ENV="production" ;;
    2) ENV="preview" ;;
    3) ENV="development" ;;
    4) ENV="production preview development" ;;
    *) echo "Invalid choice"; exit 1 ;;
esac

echo ""
echo "📝 Configuring required environment variables..."
echo ""

# AWS Region
echo "Enter AWS_REGION (e.g., us-east-1):"
read -p "> " aws_region
for env in $ENV; do
    echo "$aws_region" | vercel env add AWS_REGION $env
done

# AWS Access Key ID
echo ""
echo "Enter AWS_ACCESS_KEY_ID:"
read -p "> " aws_access_key
for env in $ENV; do
    echo "$aws_access_key" | vercel env add AWS_ACCESS_KEY_ID $env
done

# AWS Secret Access Key
echo ""
echo "Enter AWS_SECRET_ACCESS_KEY:"
read -sp "> " aws_secret_key
echo ""
for env in $ENV; do
    echo "$aws_secret_key" | vercel env add AWS_SECRET_ACCESS_KEY $env
done

# Nova Sonic Model ID
echo ""
echo "Enter NOVA_SONIC_MODEL_ID (default: amazon.nova-sonic-v1:0):"
read -p "> " model_id
model_id=${model_id:-amazon.nova-sonic-v1:0}
for env in $ENV; do
    echo "$model_id" | vercel env add NOVA_SONIC_MODEL_ID $env
done

echo ""
echo "📝 Configuring optional environment variables..."
echo ""

# Audio Cache Size
echo "Enter AUDIO_CACHE_SIZE_MB (default: 100, press Enter to skip):"
read -p "> " cache_size
if [ ! -z "$cache_size" ]; then
    for env in $ENV; do
        echo "$cache_size" | vercel env add AUDIO_CACHE_SIZE_MB $env
    done
fi

# Max Audio Duration
echo ""
echo "Enter MAX_AUDIO_DURATION_SECONDS (default: 300, press Enter to skip):"
read -p "> " max_duration
if [ ! -z "$max_duration" ]; then
    for env in $ENV; do
        echo "$max_duration" | vercel env add MAX_AUDIO_DURATION_SECONDS $env
    done
fi

# Enable Dev Mode
echo ""
echo "Enable development mode (mock audio)? (yes/no, default: no):"
read -p "> " enable_dev
if [ "$enable_dev" = "yes" ]; then
    for env in $ENV; do
        echo "true" | vercel env add ENABLE_DEV_MODE $env
    done
fi

# Log Level
echo ""
echo "Enter LOG_LEVEL (default: INFO, press Enter to skip):"
read -p "> " log_level
if [ ! -z "$log_level" ]; then
    for env in $ENV; do
        echo "$log_level" | vercel env add LOG_LEVEL $env
    done
fi

echo ""
echo "✅ Environment variables configured successfully!"
echo ""
echo "To view configured variables:"
echo "  vercel env ls"
echo ""
echo "To deploy with these variables:"
echo "  ./scripts/deploy-dev.sh    (for preview)"
echo "  ./scripts/deploy-prod.sh   (for production)"
