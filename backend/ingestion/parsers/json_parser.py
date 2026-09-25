"""
JSON parser for telemetry payloads (Slack dumps, Datadog alerts, Jira webhook exports).
"""
import json
from typing import List, Dict, Any

class JSONParser:
    @staticmethod
    def parse(content: str) -> List[Dict[str, Any]]:
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")

        records = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    records.append(item)
                else:
                    records.append({"raw_value": str(item)})
        elif isinstance(data, dict):
            # Check for Slack messages array
            if "messages" in data and isinstance(data["messages"], list):
                records.extend(data["messages"])
            # Check for Jira issues array
            elif "issues" in data and isinstance(data["issues"], list):
                records.extend(data["issues"])
            # Check for Datadog events
            elif "events" in data and isinstance(data["events"], list):
                records.extend(data["events"])
            else:
                records.append(data)
        return records
