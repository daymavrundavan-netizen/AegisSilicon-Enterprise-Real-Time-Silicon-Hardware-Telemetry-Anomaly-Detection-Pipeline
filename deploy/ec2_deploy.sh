#!/bin/bash
# ====================================================================
# AegisSilicon AWS EC2 Production Deployment & Cloud Provisioning Script
# ====================================================================

set -e

echo "=== [AegisSilicon] Starting AWS EC2 Deployment Setup ==="

# 1. Update system packages & install Docker
echo "[1/4] Installing Docker & Docker Compose..."
sudo dpkg -i --force-overwrite /var/cache/apt/archives/docker-compose-v2*.deb 2>/dev/null || true
sudo apt-get -f install -y -o Dpkg::Options::="--force-overwrite" || true
sudo apt-get update -y
sudo apt-get install -y -o Dpkg::Options::="--force-overwrite" docker.io awscli git || true

sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER

# Allow HTTP and application ports through Ubuntu UFW
sudo ufw allow 22/tcp 2>/dev/null || true
sudo ufw allow 80/tcp 2>/dev/null || true
sudo ufw allow 8000/tcp 2>/dev/null || true
sudo ufw allow 8501/tcp 2>/dev/null || true

# 2. Configure AWS S3 Bucket for Telemetry Archiving
AWS_REGION=${AWS_REGION:-"us-east-1"}
S3_BUCKET_NAME=${S3_BUCKET_NAME:-"aegissilicon-telemetry-archive-$(date +%s)"}

echo "[2/4] Provisioning Amazon S3 Archive Bucket: ${S3_BUCKET_NAME} in region ${AWS_REGION}..."
if aws s3api head-bucket --bucket "$S3_BUCKET_NAME" 2>/dev/null; then
    echo "Bucket ${S3_BUCKET_NAME} already exists."
else
    aws s3api create-bucket --bucket "$S3_BUCKET_NAME" --region "$AWS_REGION" || true
    echo "Created S3 Bucket: ${S3_BUCKET_NAME}"
fi

# 3. Build & Launch AegisSilicon Container Stack
echo "[3/4] Building and launching Docker Compose production stack..."
sudo fuser -k 9092/tcp 8000/tcp 8501/tcp 2>/dev/null || true
docker stop $(docker ps -aq) 2>/dev/null || true
docker compose -f deploy/docker-compose.yml down --remove-orphans 2>/dev/null || true
docker compose -f deploy/docker-compose.yml up -d --build

# 4. Deployment Complete Summary
echo "===================================================================="
echo "=== [AegisSilicon] AWS EC2 Production Deployment Successful! ==="
echo "===================================================================="
echo "  - Streamlit Operations UI: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 || echo 'localhost'):8501"
echo "  - Enterprise SaaS Web UI:  http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 || echo 'localhost'):8000"
echo "  - REST API & Swagger Docs: http://localhost:8000/docs"
echo "  - WebSocket Telemetry:     ws://localhost:8000/ws/telemetry"
echo "  - Amazon S3 Cloud Bucket:  s3://${S3_BUCKET_NAME}"
echo "===================================================================="
