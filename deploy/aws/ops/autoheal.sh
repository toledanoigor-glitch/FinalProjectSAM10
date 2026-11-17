#!/usr/bin/env bash
# AUTO-HEAL (prevention for incident 001): if Mabi's /health fails 2 checks in a row
# (1 minute apart), start the containers again without waiting for a human.
# Run every minute by nbu-autoheal.timer. Log: /var/log/nbu/autoheal.log (JSON lines).
# Skips while /var/lib/nbu/maintenance exists (restore-mongo.sh sets it), unless the flag is older than 30 min.
set -uo pipefail
APP=/opt/nbu/deploy/aws
STATE=/var/lib/nbu/autoheal.fails
LOG=/var/log/nbu/autoheal.log
MAINT=/var/lib/nbu/maintenance
mkdir -p /var/lib/nbu /var/log/nbu
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { echo "$1" | tee -a "$LOG"; }

if [ -e "$MAINT" ] && [ $(( $(date +%s) - $(stat -c %Y "$MAINT") )) -lt 1800 ]; then
  echo "$(now) maintenance flag set, skipping"; exit 0
fi

PREV=$(cat "$STATE" 2>/dev/null || echo 0)
if curl -sf -m 10 -o /dev/null http://localhost/health; then
  [ "$PREV" != "0" ] && log "{\"time\":\"$(now)\",\"event\":\"healthy-again\",\"after_fails\":$PREV}"
  echo 0 > "$STATE"; exit 0
fi

FAILS=$(( PREV + 1 )); echo "$FAILS" > "$STATE"
log "{\"time\":\"$(now)\",\"event\":\"health-failed\",\"fails\":$FAILS}"
[ "$FAILS" -lt 2 ] && exit 0

WAS=$(docker ps -a --filter name='^LibreChat$' --format '{{.Status}}')
cd "$APP" && docker compose up -d >/dev/null 2>&1
for i in $(seq 1 20); do curl -sf -m 5 -o /dev/null http://localhost/health && break; sleep 3; done
if curl -sf -m 10 -o /dev/null http://localhost/health; then RESULT=recovered; echo 0 > "$STATE"; else RESULT=still-down; fi
log "{\"time\":\"$(now)\",\"event\":\"restarted\",\"container_was\":\"$WAS\",\"result\":\"$RESULT\"}"
