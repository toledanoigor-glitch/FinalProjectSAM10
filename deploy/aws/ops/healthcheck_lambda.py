"""Automation #2: scheduled health check for Mabi (AWS Lambda, every 5 minutes via EventBridge).

Requests SITE_URL/health through CloudFront exactly like a user would, then publishes
NBU/Mabi HealthCheckOK (1 = answered 200, 0 = down) and HealthCheckLatencyMs.
An alarm emails the operator when HealthCheckOK stays below 1, or stops arriving.
"""
import json
import os
import time
import urllib.request

import boto3

URL = os.environ["SITE_URL"].rstrip("/") + "/health"
cloudwatch = boto3.client("cloudwatch")


def handler(event, context):
    started = time.time()
    ok, status, error = 0, None, None
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "nbu-healthcheck/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            ok = 1 if status == 200 else 0
    except Exception as exc:
        error = str(exc)[:200]
    latency_ms = int((time.time() - started) * 1000)

    cloudwatch.put_metric_data(Namespace="NBU/Mabi", MetricData=[
        {"MetricName": "HealthCheckOK", "Value": ok, "Unit": "Count"},
        {"MetricName": "HealthCheckLatencyMs", "Value": latency_ms, "Unit": "Milliseconds"},
    ])
    result = {"url": URL, "ok": ok, "status": status, "latency_ms": latency_ms, "error": error}
    print(json.dumps(result))  # goes to CloudWatch Logs /aws/lambda/nbu-healthcheck
    return result
