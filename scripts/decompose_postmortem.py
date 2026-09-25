"""
Post-Mortem Decomposer & Evaluation Preprocessor.
Decomposes a finished incident post-mortem into simulated fragmented operational streams:
- Slack conversations
- Datadog telemetry alerts
- Jira incident tickets
And organizes them into data/evaluation/incident_XXX/ for empirical validation.
"""
import json
import re
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def decompose_postmortem(postmortem_text: str, incident_name: str = "incident_001") -> Path:
    eval_dir = PROJECT_ROOT / "data" / "evaluation" / incident_name
    inputs_dir = eval_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save Ground Truth
    gt_file = eval_dir / "ground_truth.md"
    gt_file.write_text(postmortem_text, encoding="utf-8")

    # 2. Extract key entities
    # Services
    services = re.findall(r"\b([a-zA-Z0-9_\-]+(?:-service|-db|-gateway|-worker|-processor))\b", postmortem_text)
    primary_svc = services[0] if services else "order-service"

    # 3. Generate Simulated Slack Stream
    slack_stream = {
        "channel": "#incident-war-room",
        "messages": [
            {
                "timestamp": "2026-09-25T10:00:00Z",
                "user": "sre_alex",
                "text": f"@channel We are receiving high error alarms on {primary_svc}."
            },
            {
                "timestamp": "2026-09-25T10:05:00Z",
                "user": "eng_dev",
                "text": f"Looking at logs for {primary_svc}. Seeing memory pressure and container restarts."
            },
            {
                "timestamp": "2026-09-25T10:20:00Z",
                "user": "sre_alex",
                "text": f"Executing rollback on {primary_svc} to previous stable artifact."
            },
            {
                "timestamp": "2026-09-25T10:30:00Z",
                "user": "sre_alex",
                "text": f"Service {primary_svc} stabilized. Health checks passing."
            }
        ]
    }
    (inputs_dir / "slack.json").write_text(json.dumps(slack_stream, indent=2), encoding="utf-8")

    # 4. Generate Datadog Log Stream
    datadog_log = f"""2026-09-25T10:01:00Z [ALERT] datadog: {primary_svc} HTTP 5xx error rate breached 5% threshold (currently 12.4%)
2026-09-25T10:04:30Z [WARN] datadog: Host memory saturation on {primary_svc}-worker-pod-8 reached 91%
2026-09-25T10:21:00Z [INFO] datadog: Deployment rollback event received for {primary_svc}
2026-09-25T10:31:00Z [RESOLVED] datadog: {primary_svc} HTTP 5xx error rate back within normal baseline (<0.01%)"""
    (inputs_dir / "datadog.log").write_text(datadog_log, encoding="utf-8")

    # 5. Generate Jira Ticket Stream
    jira_ticket = {
        "key": f"OPS-{incident_name.upper()}",
        "fields": {
            "summary": f"Emergency Outage on {primary_svc}",
            "priority": "P1",
            "created": "2026-09-25T10:02:00Z",
            "resolutiondate": "2026-09-25T10:32:00Z",
            "description": f"Customer degradation reported on {primary_svc}. Responders mitigated via rollback."
        }
    }
    (inputs_dir / "jira.json").write_text(json.dumps(jira_ticket, indent=2), encoding="utf-8")

    print(f"Decomposed postmortem into evaluation package: {eval_dir}")
    return eval_dir

if __name__ == "__main__":
    sample_text = """# Outage Report: Order Processing Latency Spike
On September 25, 2026, order-service experienced degradation due to a memory leak in recent deployment.
Impact: 12.4% error rate across checkout. Duration: 30 minutes.
Root Cause: Unbounded cache allocation in order-service worker routine.
Mitigation: Rolling rollback to v1.9.0."""
    decompose_postmortem(sample_text, "incident_001")
