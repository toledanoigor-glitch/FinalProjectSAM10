# RUNBOOK: Mabi site is down (alarm `nbu-site-down`)

Owner: Igor Toledano (on-call admin)   Last tested: 2026-11-17 (incident 001)   Takes: about 5 minutes   Ask: Igor Toledano

## 1. WHAT THIS IS FOR
Getting the Mabi chat site back when users get an error page instead of the chat.

## 2. HOW YOU KNOW YOU NEED IT
- Email **`ALARM: "nbu-site-down" in Asia Pacific (Singapore)`**: the Lambda `nbu-healthcheck` did not get `200 OK` from `https://d2f1g5u307k6aa.cloudfront.net/health` on 2 checks in a row (one every 5 minutes; no data also counts as down).
- Or a user reports **`504 Gateway Timeout ERROR`** (CloudFront cannot reach the server).
- Normally the **auto-heal** job (`nbu-autoheal.timer`, every minute) restarts the app within about 2 minutes, before this alarm can fire. If you got this email, auto-heal did not fix it, so look carefully.

Command that shows the problem (EC2 → `nbu-itdesk-server` → Connect → Session Manager):
```
date -u; cd /opt/nbu/deploy/aws; sudo docker compose ps -a; sudo docker logs --tail 5 LibreChat
```
`LibreChat` will be `Exited` or `Restarting`, or missing.

## 3. WHAT IT AFFECTS
Everyone. No student or staff member can open Mabi or ask anything. Saved chats are safe in MongoDB; nothing is lost while it is down.

## 4. HOW TO DO IT
**Step 1: Check whether it is the whole server.** CloudWatch → Alarms. Is `nbu-status-check-failed` red too?
→ **Yes**: EC2 → Instance state → **Reboot**, wait 3 minutes, go to section 5. Docker starts both containers by itself (`restart: always`).
→ **No**: go to step 2.

**Step 2: Look at what the containers and logs say.** Run the command in section 2, and also:
```
sudo tail -5 /var/log/nbu/autoheal.log; df -h / ; free -m
```
→ You should see which of these it is:

| What you see | Cause | Do |
|---|---|---|
| `LibreChat` **Exited**, logs end normally | Container stopped (by hand, failed update, killed) | Step 3 |
| `LibreChat` **Restarting**, logs show `EACCES ... /app/logs` | Folder owner wrong: the app runs as uid 1000 | Step 4 |
| Logs show `Deployment config unavailable` | `librechat.generated.yaml` not readable (mode 600) | Step 4 |
| Disk `Use%` at 100% | Logs/backups/images filled the disk | Step 5, then step 3 |
| autoheal.log says `"result":"still-down"` | Restart is not enough; the app crashes on start | Step 4 |

**Step 3: Start the containers again.**
```
sudo docker compose up -d; sleep 15; curl -sI http://localhost/health | head -1; date -u
```
→ You should see `HTTP/1.1 200 OK`.

**Step 4: Rebuild config and fix file owners** (the start script does both):
```
sudo bash /opt/nbu/deploy/aws/start-mabi.sh
```
→ You should see both containers `Started`, then run the `curl` line from step 3.

**Step 5: Free disk space.**
```
sudo du -xh / --max-depth=2 | sort -h | tail -15
sudo docker system prune -f
```
→ `df -h /` should be well under 85%.

## 5. HOW TO CHECK IT WORKED
- [ ] `curl -sI http://localhost/health` gives `HTTP/1.1 200 OK`, and the site loads in a private browser window
- [ ] Log in and ask the system-card test question **"What time is the IT Desk open on Saturday?"** → Mabi answers "8:00 AM to 12:00 NN"
- [ ] Email `OK: "nbu-site-down"` arrives (within 10 minutes), and no new alarms for 10 minutes

## 6. HOW TO UNDO IT
- Steps 3 and 4 only start things, so there is nothing to undo. If `start-mabi.sh` broke the config, `cd /opt/nbu && git log --oneline -3`, then `git checkout <last good commit>` and run it again.
- `docker system prune` deletes only stopped containers and unused images. To get the app image back, run `start-mabi.sh` (it rebuilds it).

## 7. GOTCHAS
- **`docker stop` beats `restart: always`.** Docker does not restart a container somebody stopped. That is why auto-heal exists.
- **The alarm is slow on purpose:** 2 failed checks × 5 minutes, about 10 minutes. Do not wait for the email if a user already told you.
- **A 504 from CloudFront does not mean CloudFront is broken.** It means the server behind it is not answering.
- **Everything in the container runs as uid 1000 (`node`).** Folders created by root (`logs`, `uploads`) crash the app with `EACCES`; `start-mabi.sh` fixes the owners.
- Running `restore-mongo.sh`? It sets `/var/lib/nbu/maintenance` so auto-heal does not fight it.

## 8. CHANGE HISTORY
- 2026-11-17: written during the build; tested in incident 001 (container stopped). Added auto-heal as prevention and the step-2 table from the two real crashes during the build (EACCES, unreadable config).
