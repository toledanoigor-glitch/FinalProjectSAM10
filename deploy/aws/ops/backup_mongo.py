#!/usr/bin/env python3
"""Nightly MongoDB backup to S3 (automation #1, runs from the nbu-backup systemd timer).

1. mongodump of the LibreChat database inside the chat-mongodb container (gzip archive)
2. upload to s3://nbu-itdesk-content-842624819932/backups/mongodb/  (bucket is versioned;
   a lifecycle rule deletes backups after 14 days, so at least 7 days are always kept)
3. one JSON line to /var/log/nbu/backup.log and to CloudWatch Logs /nbu/ops/backups
4. metric NBU/Mabi BackupSuccess = 1 or 0 (an alarm fires if no successful backup in a day)
"""
import datetime as dt
import glob
import json
import os
import socket
import subprocess
import time

import boto3

REGION = "ap-southeast-1"
BUCKET = "nbu-itdesk-content-842624819932"
PREFIX = "backups/mongodb"
LOCAL_DIR = "/var/backups/nbu"
LOCAL_LOG = "/var/log/nbu/backup.log"
LOG_GROUP = "/nbu/ops/backups"
KEEP_LOCAL = 3


def main():
    session = boto3.session.Session(region_name=REGION)
    started = time.time()
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    os.makedirs(LOCAL_DIR, exist_ok=True)
    path = os.path.join(LOCAL_DIR, f"mongodb-{stamp}.archive.gz")
    key = f"{PREFIX}/{os.path.basename(path)}"
    record = {"time": stamp, "file": key, "trigger": os.environ.get("TRIGGER", "manual")}

    try:
        with open(path, "wb") as out:
            dump = subprocess.run(
                ["docker", "exec", "chat-mongodb", "mongodump", "--db", "LibreChat", "--archive", "--gzip"],
                stdout=out, stderr=subprocess.PIPE, timeout=900)
        if dump.returncode != 0:
            raise RuntimeError("mongodump failed: " + dump.stderr.decode(errors="replace")[-300:])
        size = os.path.getsize(path)
        if size < 100:
            raise RuntimeError(f"archive suspiciously small ({size} bytes)")
        session.client("s3").upload_file(path, BUCKET, key)
        record.update(status="ok", bytes=size)
    except Exception as exc:
        record.update(status="failed", error=str(exc)[:300])

    record["seconds"] = round(time.time() - started, 1)

    # keep only the newest few archives on the server's disk
    for old in sorted(glob.glob(os.path.join(LOCAL_DIR, "mongodb-*.archive.gz")))[:-KEEP_LOCAL]:
        os.remove(old)

    line = json.dumps(record)
    os.makedirs(os.path.dirname(LOCAL_LOG), exist_ok=True)
    with open(LOCAL_LOG, "a") as f:
        f.write(line + "\n")
    print(line)

    session.client("cloudwatch").put_metric_data(Namespace="NBU/Mabi", MetricData=[
        {"MetricName": "BackupSuccess", "Value": 1 if record["status"] == "ok" else 0, "Unit": "Count"}])
    logs = session.client("logs")
    stream = socket.gethostname()
    try:
        logs.create_log_stream(logGroupName=LOG_GROUP, logStreamName=stream)
    except logs.exceptions.ResourceAlreadyExistsException:
        pass
    logs.put_log_events(logGroupName=LOG_GROUP, logStreamName=stream,
                        logEvents=[{"timestamp": int(time.time() * 1000), "message": line}])

    if record["status"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
