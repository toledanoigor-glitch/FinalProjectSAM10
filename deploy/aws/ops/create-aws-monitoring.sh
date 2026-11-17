#!/usr/bin/env bash
# Create Mabi's monitoring in AWS: log groups (with retention), SNS email alerts, S3 backup
# lifecycle rule, the health-check Lambda + 5-minute schedule, 9 CloudWatch alarms and a dashboard.
#
# Run in AWS CloudShell (Singapore region), signed in as NBU-Admin:
#   git clone https://github.com/toledanoigor-glitch/FinalProjectSAM10.git nbu
#   bash nbu/deploy/aws/ops/create-aws-monitoring.sh  your.email@example.com
#
# Safe to run again: it updates what already exists.
set -euo pipefail
EMAIL="${1:?Usage: bash create-aws-monitoring.sh your.email@example.com}"
export AWS_DEFAULT_REGION="ap-southeast-1"
REGION="$AWS_DEFAULT_REGION"
HERE="$(cd "$(dirname "$0")" && pwd)"
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
BUCKET="nbu-itdesk-content-${ACCOUNT}"
SITE_URL="https://d2f1g5u307k6aa.cloudfront.net"
NS="NBU/Mabi"
TAGS='Key=Project,Value=SAM10'
INSTANCE_ID="$(aws ec2 describe-instances --filters Name=tag:Name,Values=nbu-itdesk-server Name=instance-state-name,Values=running \
  --query 'Reservations[0].Instances[0].InstanceId' --output text)"
echo "Account $ACCOUNT  Instance $INSTANCE_ID  Bucket $BUCKET"

echo "== 1. Log groups with retention (not 'Never expire')"
for spec in /nbu/mabi/app:14 /nbu/mabi/database:14 /nbu/mabi/requests:30 /nbu/ops/backups:30 /aws/lambda/nbu-healthcheck:14; do
  group="${spec%%:*}"; days="${spec##*:}"
  aws logs create-log-group --log-group-name "$group" --tags Project=SAM10 2>/dev/null || true
  aws logs put-retention-policy --log-group-name "$group" --retention-in-days "$days"
  echo "   $group  -> $days days"
done

echo "== 2. SNS topic for alerts, emailing $EMAIL"
TOPIC_ARN="$(aws sns create-topic --name nbu-alerts --tags "$TAGS" --query TopicArn --output text)"
aws sns subscribe --topic-arn "$TOPIC_ARN" --protocol email --notification-endpoint "$EMAIL" >/dev/null
echo "   $TOPIC_ARN  (CHECK YOUR INBOX and click 'Confirm subscription')"

echo "== 3. S3 lifecycle: delete backups after 14 days, old versions after 7 days"
aws s3api put-bucket-lifecycle-configuration --bucket "$BUCKET" --lifecycle-configuration '{
  "Rules": [{
    "ID": "expire-old-mongodb-backups",
    "Filter": {"Prefix": "backups/"},
    "Status": "Enabled",
    "Expiration": {"Days": 14},
    "NoncurrentVersionExpiration": {"NoncurrentDays": 7}
  }]
}'

echo "== 4. Health-check Lambda (automation #2) running every 5 minutes"
ROLE_NAME="nbu-healthcheck-lambda-role"
if ! aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
  aws iam create-role --role-name "$ROLE_NAME" --tags "$TAGS" --assume-role-policy-document '{
    "Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}' >/dev/null
  aws iam attach-role-policy --role-name "$ROLE_NAME" --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
  aws iam put-role-policy --role-name "$ROLE_NAME" --policy-name put-nbu-metrics --policy-document '{
    "Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"cloudwatch:PutMetricData","Resource":"*",
    "Condition":{"StringEquals":{"cloudwatch:namespace":"NBU/Mabi"}}}]}'
  echo "   created $ROLE_NAME, waiting for IAM to propagate..."
  sleep 15
fi
ROLE_ARN="arn:aws:iam::${ACCOUNT}:role/${ROLE_NAME}"
TMP="$(mktemp -d)"
cp "$HERE/healthcheck_lambda.py" "$TMP/lambda_function.py"
( cd "$TMP" && python3 -m zipfile -c function.zip lambda_function.py )
if aws lambda get-function --function-name nbu-healthcheck >/dev/null 2>&1; then
  aws lambda update-function-code --function-name nbu-healthcheck --zip-file "fileb://$TMP/function.zip" >/dev/null
else
  for i in 1 2 3 4 5; do
    aws lambda create-function --function-name nbu-healthcheck --runtime python3.12 --handler lambda_function.handler \
      --role "$ROLE_ARN" --zip-file "fileb://$TMP/function.zip" --timeout 20 --memory-size 128 \
      --environment "Variables={SITE_URL=$SITE_URL}" --tags Project=SAM10 >/dev/null && break
    echo "   IAM role not ready yet, retrying in 10 s ($i/5)"; sleep 10
  done
fi
aws lambda wait function-active-v2 --function-name nbu-healthcheck
RULE_ARN="$(aws events put-rule --name nbu-healthcheck-every-5-min --schedule-expression 'rate(5 minutes)' \
  --description 'Run the Mabi health check' --query RuleArn --output text)"
aws lambda add-permission --function-name nbu-healthcheck --statement-id events-invoke \
  --action lambda:InvokeFunction --principal events.amazonaws.com --source-arn "$RULE_ARN" >/dev/null 2>&1 || true
aws events put-targets --rule nbu-healthcheck-every-5-min \
  --targets "Id=nbu-healthcheck,Arn=arn:aws:lambda:${REGION}:${ACCOUNT}:function:nbu-healthcheck" >/dev/null
aws lambda invoke --function-name nbu-healthcheck "$TMP/out.json" >/dev/null && echo "   first run: $(cat "$TMP/out.json")"

echo "== 5. Alarms (all email the SNS topic, and email again when back to OK)"
alarm() { # name description namespace metric stat period evals threshold comparison missing [dimensions]
  local dims=()
  [ -n "${11:-}" ] && dims=(--dimensions "${11}")
  aws cloudwatch put-metric-alarm --alarm-name "$1" --alarm-description "$2" \
    --namespace "$3" --metric-name "$4" --statistic "$5" --period "$6" \
    --evaluation-periods "$7" --datapoints-to-alarm "$7" --threshold "$8" \
    --comparison-operator "$9" --treat-missing-data "${10}" "${dims[@]}" \
    --alarm-actions "$TOPIC_ARN" --ok-actions "$TOPIC_ARN" --tags "$TAGS"
  echo "   $1"
}
alarm nbu-cpu-high "CPU above 85% for 10 minutes: look for a stuck process or runaway loop" \
  AWS/EC2 CPUUtilization Average 300 2 85 GreaterThanThreshold notBreaching "Name=InstanceId,Value=$INSTANCE_ID"
alarm nbu-status-check-failed "EC2 status check failing: the instance or its host is unhealthy" \
  AWS/EC2 StatusCheckFailed Maximum 60 2 0 GreaterThanThreshold breaching "Name=InstanceId,Value=$INSTANCE_ID"
alarm nbu-disk-high "Root disk above 85% used: clean up logs/backups or grow the volume" \
  "$NS" DiskUsedPercent Maximum 300 1 85 GreaterThanThreshold breaching
alarm nbu-memory-high "Memory above 90% for 5 minutes: LibreChat or MongoDB may be killed" \
  "$NS" MemoryUsedPercent Average 300 1 90 GreaterThanThreshold breaching
alarm nbu-answers-failed "3 or more failed answers in 15 minutes: Mabi is up but not answering (e.g. Gemini 429/503)" \
  "$NS" AnswersFailed Sum 900 1 3 GreaterThanOrEqualToThreshold notBreaching
alarm nbu-empty-answer "An empty answer in the last 30 minutes: content or model output is missing" \
  "$NS" EmptyAnswers Sum 1800 1 0 GreaterThanThreshold notBreaching
alarm nbu-slow-answers "Average answer time above 20 s over 10 minutes: Mabi is too slow" \
  "$NS" ResponseTimeMs Average 600 1 20000 GreaterThanThreshold notBreaching
alarm nbu-site-down "Health check failed twice in a row (10 minutes): users cannot reach Mabi" \
  "$NS" HealthCheckOK Minimum 300 2 1 LessThanThreshold breaching
alarm nbu-backup-missing "No successful MongoDB backup in the last 24 hours" \
  "$NS" BackupSuccess Maximum 86400 1 1 LessThanThreshold breaching

echo "== 6. Dashboard 'Mabi-Operations'"
DASH=$(cat <<JSON
{"widgets":[
 {"type":"metric","x":0,"y":0,"width":8,"height":6,"properties":{"title":"Requests per 5 min","region":"$REGION","stat":"Sum","period":300,
   "metrics":[["$NS","Requests"],[".","AnswersOK"]]}},
 {"type":"metric","x":8,"y":0,"width":8,"height":6,"properties":{"title":"Errors per 5 min (failed / empty answers)","region":"$REGION","stat":"Sum","period":300,
   "metrics":[["$NS","AnswersFailed"],[".","EmptyAnswers"]]}},
 {"type":"metric","x":16,"y":0,"width":8,"height":6,"properties":{"title":"Response time (ms)","region":"$REGION","stat":"Average","period":300,
   "metrics":[["$NS","ResponseTimeMs"],[".","HealthCheckLatencyMs"]],
   "annotations":{"horizontal":[{"label":"slow-answer alarm","value":20000}]}}},
 {"type":"metric","x":0,"y":6,"width":8,"height":6,"properties":{"title":"CPU %","region":"$REGION","stat":"Average","period":300,
   "metrics":[["AWS/EC2","CPUUtilization","InstanceId","$INSTANCE_ID"]],"annotations":{"horizontal":[{"label":"alarm","value":85}]},"yAxis":{"left":{"min":0,"max":100}}}},
 {"type":"metric","x":8,"y":6,"width":8,"height":6,"properties":{"title":"Disk used % (root)","region":"$REGION","stat":"Maximum","period":300,
   "metrics":[["$NS","DiskUsedPercent"]],"annotations":{"horizontal":[{"label":"alarm","value":85}]},"yAxis":{"left":{"min":0,"max":100}}}},
 {"type":"metric","x":16,"y":6,"width":8,"height":6,"properties":{"title":"Memory used %","region":"$REGION","stat":"Average","period":300,
   "metrics":[["$NS","MemoryUsedPercent"]],"annotations":{"horizontal":[{"label":"alarm","value":90}]},"yAxis":{"left":{"min":0,"max":100}}}},
 {"type":"metric","x":0,"y":12,"width":8,"height":6,"properties":{"title":"Health check (1 = up)","region":"$REGION","stat":"Minimum","period":300,
   "metrics":[["$NS","HealthCheckOK"]],"yAxis":{"left":{"min":0,"max":1}}}},
 {"type":"metric","x":8,"y":12,"width":8,"height":6,"properties":{"title":"Nightly backup (1 = success)","region":"$REGION","stat":"Maximum","period":3600,
   "metrics":[["$NS","BackupSuccess"]],"yAxis":{"left":{"min":0,"max":1}}}},
 {"type":"alarm","x":16,"y":12,"width":8,"height":6,"properties":{"title":"Alarms","alarms":[
   "arn:aws:cloudwatch:$REGION:$ACCOUNT:alarm:nbu-cpu-high","arn:aws:cloudwatch:$REGION:$ACCOUNT:alarm:nbu-status-check-failed",
   "arn:aws:cloudwatch:$REGION:$ACCOUNT:alarm:nbu-disk-high","arn:aws:cloudwatch:$REGION:$ACCOUNT:alarm:nbu-memory-high",
   "arn:aws:cloudwatch:$REGION:$ACCOUNT:alarm:nbu-answers-failed","arn:aws:cloudwatch:$REGION:$ACCOUNT:alarm:nbu-empty-answer",
   "arn:aws:cloudwatch:$REGION:$ACCOUNT:alarm:nbu-slow-answers","arn:aws:cloudwatch:$REGION:$ACCOUNT:alarm:nbu-site-down",
   "arn:aws:cloudwatch:$REGION:$ACCOUNT:alarm:nbu-backup-missing"]}},
 {"type":"log","x":0,"y":18,"width":24,"height":6,"properties":{"title":"Latest requests (question, time, outcome, version)","region":"$REGION",
   "query":"SOURCE '/nbu/mabi/requests' | fields time, outcome, duration_ms, model, version, question | sort @timestamp desc | limit 20","view":"table"}}
]}
JSON
)
aws cloudwatch put-dashboard --dashboard-name Mabi-Operations --dashboard-body "$DASH" >/dev/null
echo "   https://${REGION}.console.aws.amazon.com/cloudwatch/home?region=${REGION}#dashboards/dashboard/Mabi-Operations"

echo
echo "DONE. Next: confirm the SNS email, then on the server run:  sudo bash /opt/nbu/deploy/aws/ops/install-ops.sh"
