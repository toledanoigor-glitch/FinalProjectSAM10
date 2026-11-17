#!/usr/bin/env bash
# Install Mabi's monitoring and backup jobs on the EC2 server.
# Run with:  sudo bash /opt/nbu/deploy/aws/ops/install-ops.sh
# Run AFTER deploy/aws/ops/create-aws-monitoring.sh (CloudShell) has created the log groups.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "== 1. Folders for logs, state and local backup copies"
mkdir -p /var/log/nbu /var/lib/nbu /var/backups/nbu

echo "== 2. Rotate our own log files daily, keep 14 days (stops them filling the disk)"
install -m 644 "$HERE/logrotate-nbu" /etc/logrotate.d/nbu

echo "== 3. systemd timers: request logger + auto-heal every minute, backup every night"
install -m 644 "$HERE"/systemd/*.service "$HERE"/systemd/*.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now nbu-request-metrics.timer nbu-backup.timer nbu-autoheal.timer

echo "== 4. First run of each job now (proves they work)"
python3 "$HERE/request_metrics.py"
TRIGGER=install python3 "$HERE/backup_mongo.py"

echo "== 5. Restart the app so container logs go to CloudWatch Logs"
bash "$HERE/../start-mabi.sh" >/dev/null
docker compose -f "$HERE/../docker-compose.yml" ps

echo "== Timers:"
systemctl list-timers 'nbu-*' --no-pager
