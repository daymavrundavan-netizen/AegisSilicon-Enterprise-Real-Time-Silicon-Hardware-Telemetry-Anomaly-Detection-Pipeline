# ====================================================================
# AegisSilicon AWS EC2 & S3 Deployment Script (PowerShell for Windows)
# ====================================================================

Write-Host "=== [AegisSilicon] Starting AWS EC2 Deployment Setup ===" -ForegroundColor Cyan

# 1. AWS Credentials check
try {
    aws sts get-caller-identity
    Write-Host "[AWS CLI] AWS Credentials Verified." -ForegroundColor Green
} catch {
    Write-Host "[AWS CLI] Please configure AWS CLI credentials via 'aws configure'." -ForegroundColor Yellow
}

# 2. Provision Amazon S3 Bucket
$Region = "us-east-1"
$BucketName = "aegissilicon-telemetry-archive"

Write-Host "[1/3] Provisioning Amazon S3 Bucket: $BucketName in $Region..." -ForegroundColor Cyan
aws s3api create-bucket --bucket $BucketName --region $Region

# 3. Launch Docker Compose Production Stack
Write-Host "[2/3] Building and launching Docker Compose stack..." -ForegroundColor Cyan
docker compose -f deploy/docker-compose.yml up -d --build

Write-Host "====================================================================" -ForegroundColor Green
Write-Host "=== [AegisSilicon] AWS EC2 Production Stack Running! ===" -ForegroundColor Green
Write-Host "  - Live Dashboard & API: http://localhost:8000" -ForegroundColor White
Write-Host "  - REST API Swagger Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Amazon S3 Bucket:     s3://$BucketName" -ForegroundColor White
Write-Host "====================================================================" -ForegroundColor Green
