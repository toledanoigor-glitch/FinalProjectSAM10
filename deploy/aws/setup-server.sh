#!/usr/bin/env bash
# One-time setup for a fresh Ubuntu 24.04 EC2 instance (t3.small, 2 GB RAM).
# Run with:  sudo bash deploy/aws/setup-server.sh
set -euo pipefail

echo "== 1. Swap file (2 GB) so LibreChat fits in 2 GB of RAM =="
if ! swapon --show | grep -q /swapfile; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "== 2. Packages: Docker, Compose, Python (boto3), AWS CLI =="
apt-get update -y
apt-get install -y docker.io docker-compose-v2 python3-boto3 git
command -v aws >/dev/null || snap install aws-cli --classic
systemctl enable --now docker

echo "== Done. Versions: =="
docker --version
docker compose version
aws --version
python3 -c "import boto3; print('boto3', boto3.__version__)"
free -h
