# Setup Environment Variables for Vercel (PowerShell)
# This script helps configure environment variables via Vercel CLI

$ErrorActionPreference = "Stop"

Write-Host "🔧 Setting up Vercel Environment Variables..." -ForegroundColor Cyan
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

# Select environment
Write-Host "Select environment to configure:"
Write-Host "1) Production"
Write-Host "2) Preview"
Write-Host "3) Development"
Write-Host "4) All environments"
$env_choice = Read-Host "Enter choice (1-4)"

$ENV = switch ($env_choice) {
    "1" { @("production") }
    "2" { @("preview") }
    "3" { @("development") }
    "4" { @("production", "preview", "development") }
    default { Write-Host "Invalid choice" -ForegroundColor Red; exit 1 }
}

Write-Host ""
Write-Host "📝 Configuring required environment variables..." -ForegroundColor Cyan
Write-Host ""

# AWS Region
$aws_region = Read-Host "Enter AWS_REGION (e.g., us-east-1)"
foreach ($env in $ENV) {
    $aws_region | vercel env add AWS_REGION $env
}

# AWS Access Key ID
Write-Host ""
$aws_access_key = Read-Host "Enter AWS_ACCESS_KEY_ID"
foreach ($env in $ENV) {
    $aws_access_key | vercel env add AWS_ACCESS_KEY_ID $env
}

# AWS Secret Access Key
Write-Host ""
$aws_secret_key = Read-Host "Enter AWS_SECRET_ACCESS_KEY" -AsSecureString
$aws_secret_key_plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($aws_secret_key)
)
foreach ($env in $ENV) {
    $aws_secret_key_plain | vercel env add AWS_SECRET_ACCESS_KEY $env
}

# Nova Sonic Model ID
Write-Host ""
$model_id = Read-Host "Enter NOVA_SONIC_MODEL_ID (default: amazon.nova-sonic-v1:0)"
if ([string]::IsNullOrWhiteSpace($model_id)) {
    $model_id = "amazon.nova-sonic-v1:0"
}
foreach ($env in $ENV) {
    $model_id | vercel env add NOVA_SONIC_MODEL_ID $env
}

Write-Host ""
Write-Host "📝 Configuring optional environment variables..." -ForegroundColor Cyan
Write-Host ""

# Audio Cache Size
$cache_size = Read-Host "Enter AUDIO_CACHE_SIZE_MB (default: 100, press Enter to skip)"
if (-not [string]::IsNullOrWhiteSpace($cache_size)) {
    foreach ($env in $ENV) {
        $cache_size | vercel env add AUDIO_CACHE_SIZE_MB $env
    }
}

# Max Audio Duration
Write-Host ""
$max_duration = Read-Host "Enter MAX_AUDIO_DURATION_SECONDS (default: 300, press Enter to skip)"
if (-not [string]::IsNullOrWhiteSpace($max_duration)) {
    foreach ($env in $ENV) {
        $max_duration | vercel env add MAX_AUDIO_DURATION_SECONDS $env
    }
}

# Enable Dev Mode
Write-Host ""
$enable_dev = Read-Host "Enable development mode (mock audio)? (yes/no, default: no)"
if ($enable_dev -eq "yes") {
    foreach ($env in $ENV) {
        "true" | vercel env add ENABLE_DEV_MODE $env
    }
}

# Log Level
Write-Host ""
$log_level = Read-Host "Enter LOG_LEVEL (default: INFO, press Enter to skip)"
if (-not [string]::IsNullOrWhiteSpace($log_level)) {
    foreach ($env in $ENV) {
        $log_level | vercel env add LOG_LEVEL $env
    }
}

Write-Host ""
Write-Host "✅ Environment variables configured successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "To view configured variables:"
Write-Host "  vercel env ls"
Write-Host ""
Write-Host "To deploy with these variables:"
Write-Host "  .\scripts\deploy-dev.ps1    (for preview)"
Write-Host "  .\scripts\deploy-prod.ps1   (for production)"
