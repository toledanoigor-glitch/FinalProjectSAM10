#!/usr/bin/env bash
# RESTORE TEST: rebuild the database from a backup in S3 and prove Mabi works afterwards.
# Run with:  sudo bash /opt/nbu/deploy/aws/ops/restore-mongo.sh [backup-file-name]
#   (no argument = newest backup in s3://nbu-itdesk-content-842624819932/backups/mongodb/)
#
# The current database folder is MOVED aside (not deleted), so you can undo with:
#   cd /opt/nbu/deploy/aws && docker compose down && rm -rf data-node && mv data-node.before-restore-<time> data-node && docker compose up -d
set -euo pipefail
export AWS_DEFAULT_REGION="ap-southeast-1"
BUCKET="nbu-itdesk-content-842624819932"
PREFIX="backups/mongodb"
APP="/opt/nbu/deploy/aws"
START=$(date +%s)
echo "== Restore test started $(date -u +%Y-%m-%dT%H:%M:%SZ) =="

NAME="${1:-$(aws s3 ls "s3://$BUCKET/$PREFIX/" | sort | tail -n 1 | awk '{print $4}')}"
[ -n "$NAME" ] || { echo "No backup found in s3://$BUCKET/$PREFIX/"; exit 1; }
echo "== 1. Download backup: $NAME"
aws s3 cp "s3://$BUCKET/$PREFIX/$NAME" "/tmp/$NAME" --only-show-errors

cd "$APP"
echo "== 2. Counts BEFORE (live database)"
docker exec chat-mongodb mongosh LibreChat --quiet --eval 'print("users=" + db.users.countDocuments() + " conversations=" + db.conversations.countDocuments() + " messages=" + db.messages.countDocuments())' || true

echo "== 3. Stop the stack and move the current database aside"
docker compose stop api mongodb
ASIDE="data-node.before-restore-$(date -u +%Y%m%dT%H%M%SZ)"
mv data-node "$ASIDE"
echo "   moved to $APP/$ASIDE"

echo "== 4. Start an EMPTY MongoDB and restore the backup into it"
docker compose up -d mongodb
for i in $(seq 1 30); do
  docker exec chat-mongodb mongosh --quiet --eval 'db.runCommand({ping:1}).ok' >/dev/null 2>&1 && break
  sleep 2
done
docker exec -i chat-mongodb mongorestore --archive --gzip --drop < "/tmp/$NAME"

echo "== 5. Counts AFTER restore"
docker exec chat-mongodb mongosh LibreChat --quiet --eval 'print("users=" + db.users.countDocuments() + " conversations=" + db.conversations.countDocuments() + " messages=" + db.messages.countDocuments())'

echo "== 6. Start Mabi again"
docker compose up -d api
for i in $(seq 1 45); do
  curl -sf -o /dev/null http://localhost/ && break
  sleep 2
done
curl -sI http://localhost/ | head -n 1
echo "== Restore finished in $(( $(date +%s) - START )) seconds. Now log in at the website and open an old chat."
