#!/usr/bin/env bash
# Build Mabi's config from S3, fetch secrets from Parameter Store, and (re)start the stack.
# Run with:  sudo bash deploy/aws/start-mabi.sh
# Nothing secret is stored in Git: the Gemini key lives in SSM Parameter Store (SecureString).
set -euo pipefail

REGION="ap-southeast-1"
BUCKET="nbu-itdesk-content-842624819932"
PARAM="/nbu/librechat/GOOGLE_KEY"
MODEL="gemini-3.5-flash-lite"
# Public HTTPS address of the site (CloudFront). Users never talk to the server directly.
SITE_URL="${SITE_URL:-https://d2f1g5u307k6aa.cloudfront.net}"
# Session cookies are only sent over HTTPS.
COOKIE_SECURE="${COOKIE_SECURE:-true}"
# Sign-up is closed on the public site; set ALLOW_REGISTRATION=true for one run to add an account.
ALLOW_REGISTRATION="${ALLOW_REGISTRATION:-false}"

export AWS_DEFAULT_REGION="$REGION"
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
cd "$HERE"
umask 077

echo "== 1. Build librechat.yaml from the content in s3://$BUCKET/content/ =="
# Written next to this script (not the Git-tracked librechat.yaml), so "git pull" never conflicts.
python3 "$ROOT/scripts/build_config.py" --source s3 --bucket "$BUCKET" --prefix content/ --output "$HERE/librechat.generated.yaml"
# The app runs as uid 1000 inside the container and must be able to read it (umask 077 above makes it root-only).
chmod 644 "$HERE/librechat.generated.yaml"

echo "== 2. Read the Gemini key from Parameter Store =="
GOOGLE_KEY="$(aws ssm get-parameter --name "$PARAM" --with-decryption --query Parameter.Value --output text)"

echo "== 3. Session secrets (generated once, kept only on this server) =="
if [ ! -f secrets.env ]; then
  {
    echo "CREDS_KEY=$(openssl rand -hex 32)"
    echo "CREDS_IV=$(openssl rand -hex 16)"
    echo "JWT_SECRET=$(openssl rand -hex 32)"
    echo "JWT_REFRESH_SECRET=$(openssl rand -hex 32)"
  } > secrets.env
fi

echo "== 4. Write .env (readable by root only) =="
cat > .env <<ENV
APP_TITLE=Northbridge University IT Desk
CUSTOM_FOOTER=Mabi · a SAM10 student project built on LibreChat (MIT) · Northbridge University is fictional
HELP_AND_FAQ_URL=
NO_INDEX=true
TRUST_PROXY=1
DOMAIN_CLIENT=$SITE_URL
DOMAIN_SERVER=$SITE_URL
SESSION_COOKIE_SECURE=$COOKIE_SECURE
ENDPOINTS=google
GOOGLE_KEY=$GOOGLE_KEY
GOOGLE_MODELS=$MODEL
SEARCH=false
# No extra model call per chat just to write a title (halves free-tier usage)
TITLE_CONVO=false
ALLOW_EMAIL_LOGIN=true
ALLOW_REGISTRATION=$ALLOW_REGISTRATION
ALLOW_SOCIAL_LOGIN=false
ALLOW_SOCIAL_REGISTRATION=false
ALLOW_PASSWORD_RESET=false
ENV
cat secrets.env >> .env
chmod 600 .env secrets.env

echo "== 5. Folders the app writes to =="
# LibreChat runs as user "node" (uid 1000) inside the container. Docker creates missing
# bind-mount folders as root, which made LibreChat crash with EACCES on /app/logs.
mkdir -p logs uploads
chown -R 1000:1000 logs uploads

echo "== 6. Build and start =="
docker compose up -d --build
docker compose ps
echo "Mabi should be reachable at: $SITE_URL"
