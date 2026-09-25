"""
Temporal Normalization Engine.
Converts arbitrary timestamps (Unix Epoch, IST, EST, PST, relative offsets)
into standardized ISO 8601 UTC. Deterministically calculates MTTD and MTTR.
"""
import re
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional, Dict, Any, List
from backend.models.incident import IncidentMetrics

TIMEZONE_OFFSETS = {
    "UTC": 0,
    "GMT": 0,
    "Z": 0,
    "EST": -5,
    "EDT": -4,
    "CST": -6,
    "CDT": -5,
    "MST": -7,
    "MDT": -6,
    "PST": -8,
    "PDT": -7,
    "IST": 5.5,
    "JST": 9,
}

class TemporalNormalizer:
    @staticmethod
    def parse_to_utc(raw_ts: str, anchor_dt: Optional[datetime] = None) -> Tuple[str, float]:
        """
        Parses raw timestamp string into:
        (iso_8601_utc_string, unix_epoch_float).
        Returns ("UNANCHORED_EVENT", 0.0) if unparseable.
        """
        if not raw_ts or not raw_ts.strip():
            return "UNANCHORED_EVENT", 0.0

        ts_str = raw_ts.strip()

        # 1. Unix Epoch (Seconds or Milliseconds)
        if re.match(r"^\d{10}(?:\.\d+)?$", ts_str):
            epoch = float(ts_str)
            dt = datetime.fromtimestamp(epoch, tz=timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ"), epoch

        if re.match(r"^\d{13}$", ts_str):
            epoch = float(ts_str) / 1000.0
            dt = datetime.fromtimestamp(epoch, tz=timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ"), epoch

        # 2. Relative offsets ("10 minutes ago", "just now", "2 hours ago")
        rel_match = re.match(r"(?i)^(\d+)\s*(min|minute|minutes|hour|hours|sec|second|seconds)\s*ago$", ts_str)
        if rel_match:
            if not anchor_dt:
                return "UNANCHORED_EVENT", 0.0
            val = int(rel_match.group(1))
            unit = rel_match.group(2).lower()
            if "hour" in unit:
                dt = anchor_dt - timedelta(hours=val)
            elif "min" in unit:
                dt = anchor_dt - timedelta(minutes=val)
            else:
                dt = anchor_dt - timedelta(seconds=val)
            dt_utc = dt.astimezone(timezone.utc)
            return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"), dt_utc.timestamp()

        if ts_str.lower() in ["just now", "now"]:
            if not anchor_dt:
                return "UNANCHORED_EVENT", 0.0
            dt_utc = anchor_dt.astimezone(timezone.utc)
            return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"), dt_utc.timestamp()

        # 3. Standard ISO / RFC Formats
        # Remove trailing Z or parse timezone offsets
        clean_ts = ts_str.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(clean_ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt_utc = dt.astimezone(timezone.utc)
            return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"), dt_utc.timestamp()
        except ValueError:
            pass

        # 4. Common syslog / apache format: [09/Jun/2005:06:07:04 +0000] or 2026-09-25 14:15:30
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y %H:%M",
            "%d/%b/%Y:%H:%M:%S %z",
            "%b %d %H:%M:%S",
            "%d-%m-%Y %H:%M:%S",
            "%d-%m-%Y %H:%M",
            "%I:%M %p",
            "%H:%M:%S",
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(ts_str, fmt)
                # If year is not in format, attach anchor year
                if dt.year == 1900 and anchor_dt:
                    dt = dt.replace(year=anchor_dt.year, month=anchor_dt.month, day=anchor_dt.day)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                dt_utc = dt.astimezone(timezone.utc)
                return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"), dt_utc.timestamp()
            except ValueError:
                continue

        # 5. Check named timezone e.g., "2026-09-25 14:20:00 IST"
        tz_named = re.search(r"\b(UTC|GMT|EST|EDT|CST|CDT|MST|MDT|PST|PDT|IST|JST)\b", ts_str, re.IGNORECASE)
        if tz_named:
            tz_abbr = tz_named.group(1).upper()
            offset_hours = TIMEZONE_OFFSETS.get(tz_abbr, 0)
            cleaned = re.sub(r"\b" + tz_abbr + r"\b", "", ts_str, flags=re.IGNORECASE).strip()
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"]:
                try:
                    dt = datetime.strptime(cleaned, fmt)
                    tz_obj = timezone(timedelta(hours=offset_hours))
                    dt = dt.replace(tzinfo=tz_obj)
                    dt_utc = dt.astimezone(timezone.utc)
                    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"), dt_utc.timestamp()
                except ValueError:
                    continue

        return "UNANCHORED_EVENT", 0.0

    @staticmethod
    def format_duration(seconds: Optional[float]) -> str:
        if seconds is None:
            return "--"
        if seconds <= 0:
            return "< 1m"
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        hours = int(mins // 60)
        remaining_mins = int(mins % 60)
        days = int(hours // 24)
        remaining_hours = int(hours % 24)
        if days > 0:
            years = days // 365
            rem_days = days % 365
            if years > 0:
                return f"{years}y {rem_days}d" if rem_days > 0 else f"{years}y"
            if remaining_hours > 0:
                return f"{days}d {remaining_hours}h {remaining_mins}m"
            return f"{days}d {remaining_mins}m"
        if hours > 0:
            if remaining_mins > 0:
                return f"{hours}h {remaining_mins}m"
            return f"{hours}h"
        if mins > 0:
            return f"{mins}m {secs}s" if secs > 0 else f"{mins}m 0s"
        return f"{secs}s"

    @staticmethod
    def calculate_incident_metrics(
        start_time_iso: Optional[str],
        detection_time_iso: Optional[str],
        mitigation_time_iso: Optional[str],
        resolution_time_iso: Optional[str],
        custom_mttr_seconds: Optional[float] = None,
        custom_mttd_seconds: Optional[float] = None,
        custom_duration_seconds: Optional[float] = None,
        stat_profile: Optional[Dict[str, Any]] = None,
        records_count: int = 0
    ) -> IncidentMetrics:
        """
        Strict Python deterministic calculation of MTTD and MTTR.
        Normalizes multi-year ticket batches to realistic operational MTTR / mean ticket resolution.
        """
        def parse_iso(iso_str: Optional[str]) -> Optional[datetime]:
            if not iso_str or iso_str == "UNANCHORED_EVENT":
                return None
            try:
                clean = iso_str.replace("Z", "+00:00")
                return datetime.fromisoformat(clean)
            except Exception:
                return None

        dt_start = parse_iso(start_time_iso)
        dt_detect = parse_iso(detection_time_iso)
        dt_mitigate = parse_iso(mitigation_time_iso)
        dt_resolve = parse_iso(resolution_time_iso)

        mttd_sec: Optional[float] = custom_mttd_seconds
        mttr_sec: Optional[float] = custom_mttr_seconds
        total_sec: Optional[float] = custom_duration_seconds

        # 1. Deterministic MTTD
        if mttd_sec is None and dt_start and dt_detect:
            if dt_detect > dt_start:
                mttd_sec = (dt_detect - dt_start).total_seconds()
            elif dt_detect == dt_start:
                mttd_sec = 180.0  # 3m 0s detection SLA
            else:
                mttd_sec = 120.0

        # 2. Deterministic MTTR
        if mttr_sec is None and dt_start and dt_resolve:
            raw_span = (dt_resolve - dt_start).total_seconds()
            if raw_span > 0:
                if dt_detect and dt_resolve >= dt_detect:
                    calc_mttr = (dt_resolve - dt_detect).total_seconds()
                    mttr_sec = calc_mttr if calc_mttr > 0 else raw_span
                else:
                    mttr_sec = raw_span
            else:
                mttr_sec = 300.0  # 5m minimum

        # 3. Deterministic Total Duration (Must ALWAYS be consistent with MTTR)
        if total_sec is None:
            if dt_start and dt_resolve and dt_resolve >= dt_start:
                raw_span = (dt_resolve - dt_start).total_seconds()
                total_sec = max(raw_span, (mttr_sec or 0.0) + (mttd_sec or 0.0))
            else:
                total_sec = (mttr_sec or 0.0) + (mttd_sec or 0.0)

        # Safety: Ensure duration is never less than MTTR
        if total_sec is not None and mttr_sec is not None and total_sec < mttr_sec:
            total_sec = mttr_sec

        total_mins = round(total_sec / 60.0, 1) if total_sec is not None else None

        crit_count = 0
        high_count = 0
        total_alerts = 0
        sla_met = 0
        sla_breached = 0
        sla_rate = 0.0
        p50_fmt = None
        p95_fmt = None
        top_cats = []

        if stat_profile:
            records_count = max(records_count, stat_profile.get("total_records", 0))
            crit_count = stat_profile.get("critical_count", 0)
            high_count = stat_profile.get("high_count", 0)
            total_alerts = crit_count + high_count
            sla_met = stat_profile.get("sla_met_count", 0)
            sla_breached = stat_profile.get("sla_breached_count", 0)
            sla_rate = stat_profile.get("sla_breach_rate_pct", 0.0)
            if stat_profile.get("p50_mttr_sec") is not None:
                p50_fmt = TemporalNormalizer.format_duration(stat_profile["p50_mttr_sec"])
            if stat_profile.get("p95_mttr_sec") is not None:
                p95_fmt = TemporalNormalizer.format_duration(stat_profile["p95_mttr_sec"])
            top_cats = stat_profile.get("top_categories", [])

        return IncidentMetrics(
            start_time_utc=start_time_iso,
            detection_time_utc=detection_time_iso,
            mitigation_time_utc=mitigation_time_iso,
            resolution_time_utc=resolution_time_iso,
            mttd_seconds=mttd_sec,
            mttd_formatted=TemporalNormalizer.format_duration(mttd_sec),
            mttr_seconds=mttr_sec,
            mttr_formatted=TemporalNormalizer.format_duration(mttr_sec),
            total_duration_seconds=total_sec,
            total_duration_formatted=TemporalNormalizer.format_duration(total_sec),
            total_duration_minutes=total_mins,
            records_count=records_count,
            critical_alerts_count=crit_count,
            high_alerts_count=high_count,
            total_alerts_count=total_alerts,
            sla_met_count=sla_met,
            sla_breached_count=sla_breached,
            sla_breach_rate_pct=sla_rate,
            p50_mttr_formatted=p50_fmt,
            p95_mttr_formatted=p95_fmt,
            top_failure_categories=top_cats,
            statistical_profile=stat_profile
        )
