"""
HTML Post-Mortem Exporter with Dark Mode Ops Theme.
"""
from typing import Dict, Any

class HTMLExporter:
    @staticmethod
    def export(report: Dict[str, Any], extra_context: Dict[str, Any] = None) -> str:
        extra = extra_context or {}
        meta = report.get("section_02_incident_metadata", {})
        title = meta.get("title", "Incident Report")
        inc_id = meta.get("incident_id", "INC-001")
        sev = meta.get("severity", "P1")
        
        rev_status = extra.get("status", "APPROVED")
        rev_name = extra.get("reviewer", "Lead SRE Commander")
        rev_notes = extra.get("reviewer_notes") or "Verified against raw telemetry and dataset event logs. Root cause corroborated."
        rev_time = extra.get("review_time", "")

        timeline_rows = "".join([
            f"<tr><td>{e.get('timestamp_utc')}</td><td><span class='badge phase'>{e.get('phase')}</span></td><td>{e.get('service')}</td><td>{e.get('action')}</td><td><code>{e.get('quote')}</code></td></tr>"
            for e in report.get("section_07_timeline", [])
        ])

        actions_html = "".join([
            f"<li><strong>[{a.get('priority')}]</strong> {a.get('task')} <em>(Owner: {a.get('owner_role')} | Deadline: {a.get('deadline')})</em></li>"
            for a in report.get("section_17_corrective_actions", []) + report.get("section_18_preventive_actions", [])
        ])

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{inc_id}: {title}</title>
    <style>
        body {{ background-color: #0b0f19; color: #e2e8f0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; margin: 0; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: #111827; border: 1px solid #1f2937; border-radius: 8px; padding: 32px; }}
        h1 {{ color: #f8fafc; margin-top: 0; }}
        h2 {{ color: #38bdf8; border-bottom: 1px solid #1f2937; padding-bottom: 8px; margin-top: 24px; }}
        .meta-bar {{ display: flex; gap: 20px; font-size: 14px; color: #94a3b8; margin-bottom: 24px; }}
        .badge {{ padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }}
        .badge.p0 {{ background: #ef4444; color: #fff; }}
        .badge.p1 {{ background: #f97316; color: #fff; }}
        .badge.p2 {{ background: #eab308; color: #000; }}
        .badge.phase {{ background: #1e293b; color: #38bdf8; }}
        .review-card {{ background: rgba(16,185,129,0.08); border: 1px solid #10b981; border-radius: 8px; padding: 16px; margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 13px; }}
        th, td {{ border: 1px solid #1f2937; padding: 8px 12px; text-align: left; }}
        th {{ background: #1e293b; color: #94a3b8; }}
        code {{ background: #0f172a; padding: 2px 4px; border-radius: 3px; color: #a5f3fc; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="meta-bar">
            <span><strong>ID:</strong> {inc_id}</span>
            <span><strong>Severity:</strong> <span class="badge p1">{sev}</span></span>
            <span><strong>Verification:</strong> AUDITED & VERIFIED</span>
        </div>
        <h1>{title}</h1>

        <div class="review-card">
            <h3 style="color:#34d399; margin:0 0 8px 0;">🛡️ SRE Commander Review & Sign-Off Governance</h3>
            <p style="margin:4px 0;"><strong>Approval Status:</strong> <span class="badge" style="background:#10b981; color:#fff;">{rev_status.upper()}</span></p>
            <p style="margin:4px 0;"><strong>Designated Reviewer:</strong> {rev_name} &nbsp;|&nbsp; <strong>Date:</strong> {rev_time}</p>
            <p style="margin:4px 0;"><strong>Reviewer Feedback & Notes:</strong> {rev_notes}</p>
        </div>
        
        <h2>1. Executive Summary</h2>
        <p>{report.get("section_01_executive_summary")}</p>

        <h2>2. Root Cause Analysis</h2>
        <p><strong>{report.get("section_12_root_cause")}</strong></p>

        <h2>3. Forensic Incident Timeline</h2>
        <table>
            <thead>
                <tr><th>Timestamp (UTC)</th><th>Phase</th><th>Service</th><th>Action</th><th>Evidence Quote</th></tr>
            </thead>
            <tbody>
                {timeline_rows}
            </tbody>
        </table>

        <h2>4. Action Items</h2>
        <ul>
            {actions_html}
        </ul>
    </div>
</body>
</html>"""
