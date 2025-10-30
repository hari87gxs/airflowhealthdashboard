# Slack Integration Guide

This guide explains how to set up and use Slack notifications with the Airflow Health Dashboard.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Setup](#setup)
- [Message Format](#message-format)
- [Scheduled Reports](#scheduled-reports)
- [API Endpoints](#api-endpoints)
- [Troubleshooting](#troubleshooting)

## Overview

The Airflow Health Dashboard can send automated health reports to Slack channels, providing real-time visibility into your Airflow environment's health status.

## Features

- 📊 **Rich Health Summaries**: Visual health bars, domain status, failure counts
- 🤖 **AI-Powered Analysis**: GPT-4 analysis of failures with actionable insights
- ⏰ **Scheduled Reports**: Automated reports at configurable times (default: 10 AM & 7 PM UTC)
- 🚨 **Critical Alerts**: Immediate notifications for critical health issues
- 🔗 **Dashboard Links**: Direct links to detailed dashboard views
- 🎨 **Beautiful Formatting**: Slack Block Kit for professional message layout

## Setup

### 1. Create Slack Incoming Webhook

1. Go to your Slack workspace settings
2. Navigate to **Apps** → **Manage** → **Custom Integrations** → **Incoming Webhooks**
3. Click **Add to Slack**
4. Select the channel where you want to receive notifications
5. Click **Add Incoming WebHooks Integration**
6. Copy the **Webhook URL** (looks like `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX`)

### 2. Configure Environment Variables

#### Local Development (.env file)

```bash
# Slack Configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_ENABLED=true
DASHBOARD_URL=http://localhost:3000

# Report Schedule (UTC time)
SCHEDULED_REPORTS_ENABLED=true
MORNING_REPORT_HOUR=10
MORNING_REPORT_MINUTE=0
EVENING_REPORT_HOUR=19
EVENING_REPORT_MINUTE=0
```

#### AWS Deployment (Terraform)

In `terraform/terraform.tfvars`:

```hcl
# Slack Configuration
slack_webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
dashboard_url = "https://your-dashboard.example.com"

# Report Schedule (UTC)
morning_report_hour = 10
morning_report_minute = 0
evening_report_hour = 19
evening_report_minute = 0
```

### 3. Verify Configuration

Test your Slack integration:

```bash
curl -X POST http://localhost:8000/api/slack/test \
  -H "Content-Type: application/json"
```

Expected response:
```json
{
  "success": true,
  "message": "Test message sent to Slack successfully"
}
```

## Message Format

### Health Summary Message

```
🏥 Airflow Health Dashboard Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Overall Health: ████████░░ 85% HEALTHY

Domain Health:
  ✅ domain_a: ██████████ 95% - Excellent
  ⚠️  domain_b: ████░░░░░░ 40% - Needs Attention
  ❌ domain_c: ░░░░░░░░░░ 0% - Critical

📈 Health Metrics:
  • Total DAGs: 150
  • Failed DAGs: 8
  • Success Rate: 94.7%
  • Avg Health: 85.3%

🤖 AI Analysis:
[GPT-4 powered insights about failures, patterns, and recommendations]

🔗 View Dashboard: https://your-dashboard.example.com
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generated at: 2024-01-15 10:00:00 UTC
```

### Components

1. **Header**: Emoji and title
2. **Overall Health Bar**: Visual representation of aggregate health
3. **Domain Breakdown**: Health status per domain with color-coded emojis
4. **Metrics Summary**: Key statistics
5. **AI Analysis**: Intelligent insights from GPT-4
6. **Action Button**: Link to detailed dashboard
7. **Footer**: Timestamp

## Scheduled Reports

### How It Works

The scheduler runs continuously and checks the current time every minute:

1. **Morning Report**: Triggered at configured UTC time (default 10:00)
2. **Evening Report**: Triggered at configured UTC time (default 19:00)

### Report Contents

Each scheduled report includes:

- Complete health summary for all domains
- Failed DAG analysis
- AI-powered failure insights
- Recommendations for remediation
- Direct dashboard link

### Customize Schedule

#### Via Environment Variables

```bash
# Morning report at 8:30 AM UTC
MORNING_REPORT_HOUR=8
MORNING_REPORT_MINUTE=30

# Evening report at 6:00 PM UTC
EVENING_REPORT_HOUR=18
EVENING_REPORT_MINUTE=0
```

#### Via API

```bash
# Get current schedule
curl http://localhost:8000/api/reports/schedule

# Response:
{
  "scheduled_reports_enabled": true,
  "slack_enabled": true,
  "morning_report": {
    "time": "10:00",
    "enabled": true
  },
  "evening_report": {
    "time": "19:00",
    "enabled": true
  },
  "dashboard_url": "https://dashboard.example.com",
  "current_time": "14:23:45",
  "timezone": "UTC"
}
```

### Manual Trigger

Send reports on-demand:

```bash
curl -X POST http://localhost:8000/api/reports/send
```

## API Endpoints

### Test Slack Connection

**POST** `/api/slack/test`

Tests the Slack webhook configuration.

```bash
curl -X POST http://localhost:8000/api/slack/test
```

Response:
```json
{
  "success": true,
  "message": "Test message sent to Slack successfully"
}
```

### Send Manual Report

**POST** `/api/reports/send`

Triggers an immediate health report to Slack.

```bash
curl -X POST http://localhost:8000/api/reports/send
```

Response:
```json
{
  "success": true,
  "message": "Report sent to Slack successfully",
  "domains_analyzed": 15,
  "total_failures": 23
}
```

### Get Report Schedule

**GET** `/api/reports/schedule`

Returns current report schedule configuration.

```bash
curl http://localhost:8000/api/reports/schedule
```

Response:
```json
{
  "scheduled_reports_enabled": true,
  "slack_enabled": true,
  "morning_report": {
    "time": "10:00",
    "enabled": true
  },
  "evening_report": {
    "time": "19:00",
    "enabled": true
  },
  "dashboard_url": "https://dashboard.example.com",
  "current_time": "14:23:45",
  "timezone": "UTC"
}
```

## Troubleshooting

### Messages Not Appearing in Slack

**Check webhook URL:**
```bash
echo $SLACK_WEBHOOK_URL
```

Should start with `https://hooks.slack.com/services/`

**Verify Slack integration is enabled:**
```bash
curl http://localhost:8000/api/reports/schedule | jq '.slack_enabled'
```

Should return `true`

**Test connection:**
```bash
curl -X POST http://localhost:8000/api/slack/test
```

**Check logs:**
```bash
# Docker
docker logs airflow-health-dashboard-backend-1

# AWS ECS
aws logs tail /ecs/airflow-health-dashboard --follow --filter-pattern "slack"
```

### Scheduled Reports Not Sending

**Verify scheduled reports are enabled:**
```bash
curl http://localhost:8000/api/reports/schedule | jq '.scheduled_reports_enabled'
```

**Check scheduler is running:**

For Docker:
```bash
docker ps | grep scheduler
```

For AWS:
```bash
aws ecs list-tasks --cluster airflow-health-dashboard-cluster --service-name scheduler
```

**Verify time configuration:**
```bash
curl http://localhost:8000/api/reports/schedule | jq '.morning_report, .evening_report'
```

**Check scheduler logs:**
```bash
# Docker
docker logs airflow-health-dashboard-scheduler-1

# AWS
aws logs tail /ecs/airflow-health-dashboard --follow --filter-pattern "scheduler"
```

### Incorrect Time Zone

All times are in **UTC**. To convert from your local time:

```bash
# Convert local time to UTC
# Example: 10 AM PST = 6 PM UTC (10 + 8 hours)
MORNING_REPORT_HOUR=18
```

Or use this helper:
```bash
# Get current UTC time
date -u

# Your timezone offset
TZ=America/Los_Angeles date
```

### Webhook URL Invalid

**Error:** `"Slack webhook URL is not configured"`

**Solution:**
1. Check environment variable is set:
   ```bash
   echo $SLACK_WEBHOOK_URL
   ```

2. Verify in configuration:
   ```bash
   curl http://localhost:8000/api/reports/schedule | jq '.slack_enabled'
   ```

3. Restart service after updating:
   ```bash
   # Docker
   docker-compose restart backend scheduler
   
   # AWS
   aws ecs update-service --cluster $CLUSTER --service scheduler --force-new-deployment
   ```

### Message Formatting Issues

If messages appear broken in Slack:

1. **Check Block Kit compatibility**: Ensure your Slack workspace allows rich formatting
2. **Verify webhook permissions**: Webhook must have permission to post formatted messages
3. **Test with simple message**: Use the `/api/slack/test` endpoint

### Rate Limiting

Slack has rate limits for incoming webhooks:

- **1 message per second** per webhook
- **Burst**: Up to 30 messages in 1 minute

If you hit limits:

1. **Reduce report frequency**
2. **Batch multiple insights** into single message
3. **Use Slack API** instead of webhooks for higher limits

## Advanced Configuration

### Custom Message Templates

To customize message appearance, edit `backend/app/slack_service.py`:

```python
def _format_health_summary_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
    # Customize blocks here
    blocks = [
        # Your custom blocks
    ]
    return {"blocks": blocks}
```

### Multiple Slack Channels

To send to multiple channels, create multiple webhook URLs:

```bash
SLACK_WEBHOOK_URL_PRIMARY=https://hooks.slack.com/services/T00/B00/XXX
SLACK_WEBHOOK_URL_ALERTS=https://hooks.slack.com/services/T00/B01/YYY
```

Then update `slack_service.py` to use both.

### Conditional Notifications

Send notifications only when health is below threshold:

```python
# In scheduler.py
if health_summary['overall_health'] < 70:
    await slack_service.send_health_summary(health_summary)
```

## Best Practices

1. **Choose appropriate channel**: Use dedicated `#airflow-health` channel
2. **Set reasonable schedules**: Twice daily is usually sufficient
3. **Monitor webhook usage**: Check Slack app analytics
4. **Include context**: Dashboard links help teams investigate
5. **Test before production**: Use `/api/slack/test` endpoint
6. **Document for team**: Share this guide with your team
7. **Set up alerts**: Configure critical health thresholds

## Example Use Cases

### Daily Standup Integration

Schedule morning report at team standup time:
```bash
MORNING_REPORT_HOUR=9  # 9 AM UTC
MORNING_REPORT_MINUTE=0
```

### On-Call Rotation

Send evening report before on-call shift:
```bash
EVENING_REPORT_HOUR=17  # 5 PM UTC
EVENING_REPORT_MINUTE=45
```

### Weekend Monitoring

Disable scheduled reports on weekends in code:
```python
# In scheduler.py
if datetime.utcnow().weekday() in [5, 6]:  # Saturday, Sunday
    return  # Skip report
```

### Incident Response

Manually trigger report during incidents:
```bash
curl -X POST http://localhost:8000/api/reports/send
```

## Resources

- [Slack Incoming Webhooks Documentation](https://api.slack.com/messaging/webhooks)
- [Slack Block Kit Builder](https://app.slack.com/block-kit-builder)
- [Slack Rate Limits](https://api.slack.com/docs/rate-limits)

## Support

For issues with Slack integration:

1. Check this troubleshooting guide
2. Review application logs
3. Test webhook manually:
   ```bash
   curl -X POST $SLACK_WEBHOOK_URL \
     -H 'Content-Type: application/json' \
     -d '{"text": "Test message"}'
   ```
4. Open GitHub issue with logs and error details
