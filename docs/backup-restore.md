# Backup and restore: Mabi (Northbridge University IT Desk)

## What must be backed up, and how

| What | Where it lives | How it is protected | Restored by |
|---|---|---|---|
| Chats, users, settings (MongoDB `LibreChat`) | EC2 `/opt/nbu/deploy/aws/data-node` | `mongodump` every night 02:00 Manila (18:00 UTC) by systemd timer `nbu-backup.timer`, uploaded to `s3://nbu-itdesk-content-842624819932/backups/mongodb/` | `deploy/aws/ops/restore-mongo.sh` |
| IT Desk knowledge (`content/*.md`) | S3 `content/` + git | S3 versioning is on; copy in git | Re-upload from git, or restore an older S3 version |
| App config (`librechat.yaml`, compose, scripts) | git (GitHub) | Version history in git; `librechat.generated.yaml` is rebuilt from S3 at every start | `git clone` + `start-mabi.sh` |
| Gemini API key | SSM Parameter Store `/nbu/librechat/GOOGLE_KEY` (SecureString) | Never on disk in git; AWS keeps it | Read again by `start-mabi.sh` |
| Session/JWT secrets | EC2 `deploy/aws/secrets.env` (mode 600) | **Not backed up on purpose.** If lost, new ones are made and users just log in again | `start-mabi.sh` creates new ones |
| Uploaded files | EC2 `deploy/aws/uploads` | Not backed up (file uploads are not used by Mabi) | n/a: known gap |

Retention: 3 newest backups kept on the server, backups in S3 expire after 14 days (lifecycle rule), old S3 versions after 7 days.
Each backup writes a JSON line to `/var/log/nbu/backup.log` and CloudWatch log group `/nbu/ops/backups`, and sends metric `NBU/Mabi BackupSuccess`. Alarm `nbu-backup-missing` emails if there is no successful backup in 1 day.

## Targets

| | Target | Measured on 2026-11-17 |
|---|---|---|
| **RPO** (how much data we can lose) | 24 hours (one nightly backup) | Lost exactly the chats made after the last backup (1 conversation, 2 messages) |
| **RTO** (how long to get the chat back) | 15 minutes | **43 seconds** (script start to site answering 200 OK), plus logging in |

## Restore test: 2026-11-17 (real run)

| Time (UTC) | Step | Result |
|---|---|---|
| 09:18:18 | Manual backup `sudo python3 /opt/nbu/deploy/aws/ops/backup_mongo.py` | `status ok`, 27,192 bytes, 1.0 s, file `backups/mongodb/mongodb-2026-11-17T09-18-18Z.archive.gz` |
| ~09:20 | Asked Mabi a **new** question after the backup ("How do I connect to NBU-Secure Wi-Fi?") | This chat is NOT in the backup, so it should disappear |
| 09:21:41 | `sudo bash /opt/nbu/deploy/aws/ops/restore-mongo.sh` started | Downloaded newest backup from S3 |
| 09:21:41 | Counts before | users=1, conversations=**7**, messages=**18** |
| 09:21:59 | Stack stopped, live data moved aside to `data-node.before-restore-20261117T092159Z` (not deleted) | |
| 09:22:03–09:22:10 | Empty MongoDB started, `mongorestore --drop` | **93 documents restored, 0 failed** |
| 09:22:10 | Counts after | users=1, conversations=**6**, messages=**16** |
| ~09:22:24 | Mabi started, `curl` health check | `HTTP/1.1 200 OK`. **Restore finished in 43 seconds** |
| 09:25 | Checked in browser | Old chats are back, the Wi-Fi chat is gone, as expected |

Evidence: `backup-manual.png`, `restore-counts-before.png`, `restore-output.png`, `restore-chats-back.png`.

**What this proves:** the backup in S3 can really be restored into an empty database, the app works afterwards, and anything written after the last backup is lost (that is the RPO).

## How to restore (runbook)

1. Open EC2 → `nbu-itdesk-server` → Connect → Session Manager.
2. Newest backup: `sudo bash /opt/nbu/deploy/aws/ops/restore-mongo.sh`
   A specific backup: `sudo bash /opt/nbu/deploy/aws/ops/restore-mongo.sh mongodb-YYYY-MM-DDTHH-MM-SSZ.archive.gz`
   (list them: `aws s3 ls s3://nbu-itdesk-content-842624819932/backups/mongodb/`)
3. Wait for `Restore finished in N seconds` and `HTTP/1.1 200 OK`.
4. Open the site, log in, open an old chat.
5. **Undo** (if the restore was a mistake): stop the stack, move `data-node` away, rename `data-node.before-restore-<time>` back to `data-node`, start again (exact commands are at the top of the script).

## Whole server lost (not tested)

1. Launch a new Ubuntu 24.04 t3.small with the same IAM role and security group.
2. `git clone` the repo to `/opt/nbu`, run `deploy/aws/setup-server.sh`, then `deploy/aws/start-mabi.sh` (config from S3, key from Parameter Store, new session secrets).
3. Run `restore-mongo.sh` to bring back the chats from S3.
4. Point the CloudFront origin to the new server's public DNS.

Estimated 20–30 minutes. This path has **not** been rehearsed; only the database restore above was tested.
