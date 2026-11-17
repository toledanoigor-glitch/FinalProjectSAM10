#!/usr/bin/env python3
"""Mabi request logger and custom metrics (runs every minute from a systemd timer).

For every answer Mabi produced since the last run it writes one JSON line:
    the question asked, how long the answer took, whether it succeeded, and which version answered
to /var/log/nbu/requests.log and to the CloudWatch log group /nbu/mabi/requests.

It also publishes these custom metrics to the CloudWatch namespace NBU/Mabi:
    Requests, AnswersOK, AnswersFailed, EmptyAnswers, ResponseTimeMs, DiskUsedPercent, MemoryUsedPercent

All questions in this system are invented test data (Northbridge University is fictional).
"""
import datetime as dt
import json
import os
import shutil
import socket
import subprocess
import sys

import boto3

REGION = "ap-southeast-1"
NAMESPACE = "NBU/Mabi"
LOG_GROUP = "/nbu/mabi/requests"
LOCAL_LOG = "/var/log/nbu/requests.log"
STATE_FILE = "/var/lib/nbu/request_metrics.state"
REPO = "/opt/nbu"
SETTLE_SECONDS = 20  # skip answers updated in the last 20 s; they may still be streaming

MONGO_QUERY = r"""
const since = ISODate("%(since)s"), until = ISODate("%(until)s");
const out = db.messages.find({isCreatedByUser: false, updatedAt: {$gt: since, $lte: until}}).toArray().map(m => {
  const p = m.parentMessageId ? db.messages.findOne({messageId: m.parentMessageId}) : null;
  const parts = (m.content || []);
  const textParts = parts.filter(c => c && c.type === 'text')
                         .map(c => typeof c.text === 'string' ? c.text : ((c.text && c.text.value) || ''));
  const errorParts = parts.filter(c => c && c.type === 'error');
  const answer = ((m.text || '') + textParts.join('')).trim();
  return {
    id: m.messageId, conversation: m.conversationId,
    question: p ? (p.text || '') : '',
    asked: p ? p.createdAt : m.createdAt, answered: m.updatedAt,
    model: m.model || null, endpoint: m.endpoint || null,
    error: !!m.error || errorParts.length > 0, unfinished: !!m.unfinished,
    answer_chars: answer.length,
    error_text: (m.error || errorParts.length) ? JSON.stringify(errorParts.length ? errorParts : (m.text || '')).slice(0, 300) : ''
  };
});
print(EJSON.stringify(out, {relaxed: true}));
"""


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def parse_time(value):
    if isinstance(value, dict) and "$date" in value:
        value = value["$date"]
    if isinstance(value, (int, float)):
        return dt.datetime.fromtimestamp(value / 1000, dt.timezone.utc)
    return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def app_version():
    try:
        commit = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                                capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        commit = "unknown"
    return f"librechat-v0.8.9-rc1+nbu-{commit or 'unknown'}"


def memory_used_percent():
    info = {}
    with open("/proc/meminfo") as f:
        for line in f:
            key, value = line.split(":", 1)
            info[key] = int(value.strip().split()[0])
    return round((info["MemTotal"] - info["MemAvailable"]) / info["MemTotal"] * 100, 2)


def disk_used_percent(path="/"):
    usage = shutil.disk_usage(path)
    return round(usage.used / usage.total * 100, 2)


def read_answers(since, until):
    js = MONGO_QUERY % {"since": iso(since), "until": iso(until)}
    result = subprocess.run(["docker", "exec", "chat-mongodb", "mongosh", "LibreChat", "--quiet", "--eval", js],
                            capture_output=True, text=True, timeout=50)
    if result.returncode != 0:
        raise RuntimeError(f"mongosh failed: {result.stderr.strip()[:300]}")
    lines = [l for l in result.stdout.strip().splitlines() if l.strip()]
    return json.loads(lines[-1]) if lines else []


def ship_logs(logs, events):
    if not events:
        return
    stream = f"{socket.gethostname()}-{dt.datetime.utcnow():%Y-%m-%d}"
    try:
        logs.create_log_stream(logGroupName=LOG_GROUP, logStreamName=stream)
    except logs.exceptions.ResourceAlreadyExistsException:
        pass
    events.sort(key=lambda e: e["timestamp"])
    logs.put_log_events(logGroupName=LOG_GROUP, logStreamName=stream, logEvents=events)


def main():
    now = dt.datetime.now(dt.timezone.utc)
    until = now - dt.timedelta(seconds=SETTLE_SECONDS)
    try:
        since = parse_time(open(STATE_FILE).read().strip())
    except Exception:
        since = until - dt.timedelta(minutes=2)

    version = app_version()
    records = []
    try:
        answers = read_answers(since, until)
    except Exception as exc:  # database unreachable is itself a failure signal
        print(f"WARN could not read MongoDB: {exc}", file=sys.stderr)
        answers = None

    ok = failed = empty = 0
    durations = []
    for a in answers or []:
        asked, answered = parse_time(a["asked"]), parse_time(a["answered"])
        duration_ms = max(0, int((answered - asked).total_seconds() * 1000))
        if a["error"]:
            outcome = "failed"
            failed += 1
        elif a["answer_chars"] == 0 and not a["unfinished"]:
            outcome = "empty"
            empty += 1
        else:
            outcome = "ok"
            ok += 1
        durations.append(duration_ms)
        records.append({
            "time": iso(answered),
            "question": a["question"][:300],
            "duration_ms": duration_ms,
            "outcome": outcome,
            "model": a["model"],
            "endpoint": a["endpoint"],
            "version": version,
            "conversation": a["conversation"],
            "error": a["error_text"],
        })

    os.makedirs(os.path.dirname(LOCAL_LOG), exist_ok=True)
    with open(LOCAL_LOG, "a") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    metrics = [
        {"MetricName": "DiskUsedPercent", "Value": disk_used_percent(), "Unit": "Percent"},
        {"MetricName": "MemoryUsedPercent", "Value": memory_used_percent(), "Unit": "Percent"},
    ]
    if answers is not None:
        metrics += [
            {"MetricName": "Requests", "Value": len(records), "Unit": "Count"},
            {"MetricName": "AnswersOK", "Value": ok, "Unit": "Count"},
            {"MetricName": "AnswersFailed", "Value": failed, "Unit": "Count"},
            {"MetricName": "EmptyAnswers", "Value": empty, "Unit": "Count"},
        ]
        if durations:
            metrics.append({"MetricName": "ResponseTimeMs", "Value": sum(durations) / len(durations),
                            "Unit": "Milliseconds"})

    session = boto3.session.Session(region_name=REGION)
    session.client("cloudwatch").put_metric_data(Namespace=NAMESPACE, MetricData=metrics)
    ship_logs(session.client("logs"), [
        {"timestamp": int(parse_time(r["time"]).timestamp() * 1000), "message": json.dumps(r, ensure_ascii=False)}
        for r in records
    ])

    if answers is not None:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, "w") as f:
            f.write(iso(until))
    print(f"{iso(now)} requests={len(records)} ok={ok} failed={failed} empty={empty} "
          f"disk={metrics[0]['Value']}% mem={metrics[1]['Value']}%")


if __name__ == "__main__":
    main()
