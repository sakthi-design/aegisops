"""
Ingestion Gateway: Source Type Detection Engine.
Identifies whether operational data originated from Slack, Datadog, CloudWatch,
Jira, ServiceNow, CI/CD, Logs, Emails, or Markdown runbooks.
"""
import re
import json
from typing import Dict, Any

class SourceDetector:
    @staticmethod
    def detect(content: str, filename: str = "") -> str:
        lower_name = filename.lower()
        lower_content = content.lower()

        # 1. Filename heuristic
        if "slack" in lower_name:
            return "slack"
        if "datadog" in lower_name:
            return "datadog"
        if "cloudwatch" in lower_name:
            return "cloudwatch"
        if "jira" in lower_name:
            return "jira"
        if "servicenow" in lower_name:
            return "servicenow"
        if "cicd" in lower_name or "deploy" in lower_name:
            return "cicd"
        if lower_name.endswith(".csv"):
            return "csv"

        # 2. JSON structure heuristic
        if content.strip().startswith("{") or content.strip().startswith("["):
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    if "attachments" in parsed or "client_msg_id" in parsed or "channel" in parsed:
                        return "slack"
                    if "alert_type" in parsed or "org" in parsed or "snapshot" in parsed or "event_type" in parsed:
                        return "datadog"
                    if "AlarmName" in parsed or "NewStateValue" in parsed:
                        return "cloudwatch"
                    if "fields" in parsed and "issuetype" in parsed.get("fields", {}):
                        return "jira"
                    if "workflow" in parsed or "commit" in parsed or "pipeline" in parsed:
                        return "cicd"
            except Exception:
                pass

        # 3. Content regex heuristic
        if re.search(r"\b(slack|channel|@here|@channel|thread_ts|posted in #)\b", lower_content):
            return "slack"
        if re.search(r"\b(datadog|monitor alert|datadog alert|p99 latency threshold breached)\b", lower_content):
            return "datadog"
        if re.search(r"\b(cloudwatch|alarm:|alarmname|arn:aws:cloudwatch)\b", lower_content):
            return "cloudwatch"
        if re.search(r"\b(jira|issue-[0-9]+|priority:\s*p[0-4]|ticket assigned to)\b", lower_content):
            return "jira"
        if re.search(r"\b(github actions|gitlab-ci|jenkins build|git commit|deployed commit [0-9a-f]{7,40})\b", lower_content):
            return "cicd"
        if re.search(r"^(from:|to:|subject:|date:)", lower_content, re.MULTILINE):
            return "email"
        if lower_name.endswith(".log") or re.search(r"\[(error|warn|info|fatal|debug)\]", lower_content):
            return "application_log"

        return "generic_telemetry"
