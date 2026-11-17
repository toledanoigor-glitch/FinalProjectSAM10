# Incident 001: Mabi site down (container stopped)

**Date:** 2026-11-17   **Severity:** whole service down   **Owner:** Igor Toledano   **Status:** resolved, prevention in place and tested
**Type:** fault created on purpose (brief Section 3.7 allows this) to test that monitoring catches it and that the runbook works.

## Summary
At 09:29:12 UTC the LibreChat application container on `nbu-itdesk-server` stopped. Users of `https://d2f1g5u307k6aa.cloudfront.net` got `504 Gateway Timeout ERROR` from CloudFront. The database kept running and no chats were lost. The CloudWatch alarm `nbu-site-down` emailed the admin 10 min 14 s later, and the admin restored the service 3 min 15 s after the email by following the runbook. Total outage: **13 min 29 s**.

## Timeline (UTC; Manila = UTC+8)
| Time | What happened | Evidence |
|---|---|---|
| 09:29:12 | `sudo docker stop LibreChat`: app shuts down (`Graceful shutdown complete, exiting`) | `fault-start.png`, `fault-fix.png` (logs) |
| ~09:30 | Site shows `504 Gateway Timeout ERROR` (CloudFront cannot reach the origin) | `fault-site-down.png` |
| 09:34:00 | Lambda `nbu-healthcheck`: 2nd failed check (`HealthCheckOK = 0` for 09:29 and 09:34 periods) | alarm email text |
| **09:39:26** | **Alarm `nbu-site-down` → ALARM, email to admin** | `fault-alarm-email.png` |
| 09:41:51 | Admin starts runbook step 2: `docker compose ps -a` shows `LibreChat Exited (0) 12 minutes ago`, `chat-mongodb Up` | `fault-fix.png` |
| 09:42 | `docker logs -n 5 LibreChat`: clean shutdown at 09:29:12, no crash or error | `fault-fix.png` |
| 09:42 | Runbook step 3: `docker compose up -d` | `fault-fix.png` |
| **09:42:41** | **`curl -sI http://localhost/health` → `HTTP/1.1 200 OK`. Service restored** | `fault-fix.png` |
| later | Alarm returns to OK, email `OK: "nbu-site-down"` | `fault-ok-email.png` |

| Measure | Value |
|---|---|
| **Time to detect** (fault started → alarm fired) | **10 min 14 s** |
| **Time to fix** (alarm fired → fixed) | **3 min 15 s** |
| Total outage | 13 min 29 s |
| Data lost | none (MongoDB stayed up) |

## Root cause
The app container received a stop signal and exited cleanly (exit code 0). This is the same as an admin stopping it by mistake, a failed update leaving it stopped, or Docker being told to stop it during maintenance.

**Why it stayed down:** the compose file uses `restart: always`, but Docker deliberately does **not** restart a container that was stopped with `docker stop`; the policy only covers crashes and reboots. Nothing else on the server watched whether the app answered. The only check was the external health check, which is designed to **alert a human** (2 failures × 5 minutes, so it does not page on a single blip). So the service stayed down until a person read the email and logged in: 13½ minutes.

Chain: *container stopped → restart policy does not apply to a manual stop → no local watchdog → only an email to a human → about 13 minutes of 504s.*

## Fix
Runbook `docs/runbook-site-down.md`, steps 2–3: check `docker compose ps -a` and the logs, then `docker compose up -d`, then check `/health`.

## Prevention: auto-heal
New automation `deploy/aws/ops/autoheal.sh`, run every minute by systemd timer `nbu-autoheal.timer`:
- checks `http://localhost/health` on the server itself;
- after **2 failures in a row** (so one slow answer does not trigger it) runs `docker compose up -d` and checks again;
- writes JSON lines to `/var/log/nbu/autoheal.log`;
- pauses while `restore-mongo.sh` runs (flag file `/var/lib/nbu/maintenance`), so it never fights a planned restore.

The CloudWatch alarm stays as the second line of defence: if auto-heal cannot fix it (for example the app crashes on start), the human still gets the email.

## Evidence that the prevention works (same fault, repeated)
| Time (UTC) | Event (from `/var/log/nbu/autoheal.log`) |
|---|---|
| 09:47:25 | `sudo docker stop LibreChat` (same fault again) |
| 09:47:48 | `health-failed`, fails 1 |
| 09:48:53 | `health-failed`, fails 2 |
| **09:49:03** | **`restarted`, `container_was: "Exited (0) About a minute ago"`, `result: recovered`** |

| | Before prevention | After prevention |
|---|---|---|
| Outage for the same fault | 13 min 29 s | **1 min 38 s** |
| Human needed | yes | no |

Evidence: `autoheal-installed.png`, `autoheal-proof.png`.

## Lessons
1. `restart: always` is not a watchdog. A local health check that acts is worth more than an alert that waits for a person.
2. The 10-minute alarm delay is on purpose (no paging on one bad check). With auto-heal, short outages now end before the alarm fires, and the alarm only reaches a human for problems a restart cannot fix.
3. The first `docker logs` command broke when pasted into Session Manager (`--tail` was cut). The runbook now uses the shorter `docker logs -n 5`, one command per line.

## Two earlier real faults found during the build (no monitoring yet, so no timings)
| Fault | Root cause | Fix and prevention |
|---|---|---|
| App crash loop, `EACCES: permission denied, mkdir '/app/logs'`, CloudFront 504 | The app runs as uid 1000 (`node`), but Docker created the bind-mounted `logs/` and `uploads/` folders as root | `start-mabi.sh` now runs `chown -R 1000:1000 logs uploads` before every start |
| `Deployment config unavailable for storage selection` | Start script uses `umask 077`, so the generated `librechat.generated.yaml` was mode 600 (root only) and uid 1000 could not read it | `start-mabi.sh` now runs `chmod 644` on the generated config; added to runbook step 2 table |
