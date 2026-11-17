# Runbook: Mabi site is down (alarm `nbu-site-down`)

| | |
|---|---|
| **Alert** | Email `ALARM: "nbu-site-down" in Asia Pacific (Singapore)` |
| **What it means** | The Lambda `nbu-healthcheck` could not get `200 OK` from `https://d2f1g5u307k6aa.cloudfront.net/health` 2 times in a row (checked every 5 minutes). Missing data also counts as down. |
| **What users see** | `504 Gateway Timeout ERROR` from CloudFront, or the page does not load |
| **Who** | On-call admin (Igor Toledano), working as IAM user `igor` → role `NBU-Admin` |
| **Target** | Back up within 15 minutes of the alert |

## 1. Confirm (1 minute)
1. Open the site in a private window. Is it really down (504 / 502 / not loading)?
2. CloudWatch → Alarms: is `nbu-status-check-failed` also red?
   - **Yes** → the whole server is sick: go to step 4.
   - **No** → the server is fine, the app is not: go to step 2.

## 2. Look (2 minutes)
EC2 → `nbu-itdesk-server` → Connect → Session Manager:
```
date -u
cd /opt/nbu/deploy/aws
sudo docker compose ps -a          # is LibreChat "Exited" or "Restarting"?
sudo docker logs --tail 30 LibreChat
df -h /  ;  free -m                # disk full? out of memory?
```
| What you see | Likely cause | Go to |
|---|---|---|
| `LibreChat` **Exited**, logs end normally | Container was stopped (by hand, or the update failed) | 3a |
| `LibreChat` **Restarting**, logs show `EACCES ... /app/logs` | Folder owner wrong (app runs as uid 1000) | 3b |
| Logs show `Deployment config unavailable` | `librechat.generated.yaml` not readable | 3b |
| Disk at 100% | Logs or backups filled the disk | 3c |
| `chat-mongodb` **Exited** | Database down | 3a |

## 3. Fix
**3a. Start it again**
```
sudo docker compose up -d
```
**3b. Fix file owners and rebuild config** (the start script does both)
```
sudo bash /opt/nbu/deploy/aws/start-mabi.sh
```
**3c. Disk full**
```
sudo du -xh / --max-depth=2 | sort -h | tail -15
sudo docker system prune -f            # removes stopped containers and old images
sudo ls -lh /var/backups/nbu           # only 3 should be kept
```
Then do 3a.

## 4. Whole server sick
EC2 → Instance state → **Reboot**. Docker starts both containers by itself (`restart: always`). Wait 3 minutes, then go to step 5. If it still fails, see "Whole server lost" in `backup-restore.md`.

## 5. Check it is fixed
```
sleep 15; curl -sI http://localhost/health | head -1     # want: HTTP/1.1 200 OK
date -u
```
- Open the site, log in, ask one test question ("What time is the IT Desk open on Saturday?").
- Wait for the email `OK: "nbu-site-down"` (up to 10 minutes).

## 6. Afterwards
- Write down: time of alert, time you started, time fixed, cause, fix. Use `docs/incident-001-site-down.md` as the example.
- If the cause was new, add a row to the table in step 2.

## Escalate
If not fixed in 30 minutes: tell the course instructor / IT lead, put a notice on the website, and keep the incident notes.
