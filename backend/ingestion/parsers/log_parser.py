"""
Log parser for unstructured and semi-structured server and application logs.
"""
import re
from typing import List, Dict, Any

class LogParser:
    # Matches common timestamped log patterns:
    # 2026-09-25 14:15:30,123 [ERROR] service.py - Message
    # [Thu Jun 09 06:07:04 2005] [notice] worker restarting
    LOG_REGEX = re.compile(
        r"^(?:\[(?P<timestamp1>[^\]]+)\]|(?P<timestamp2>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?))\s*"
        r"(?:\[(?P<level>[A-Za-z]+)\])?\s*"
        r"(?P<message>.*)$"
    )

    @classmethod
    def parse(cls, content: str, max_records: int = 5000) -> List[Dict[str, Any]]:
        import io
        records = []
        count = 0
        for line in io.StringIO(content):
            line_str = line.strip()
            if not line_str:
                continue
            count += 1
            if count <= max_records:
                match = cls.LOG_REGEX.match(line_str)
                if match:
                    d = match.groupdict()
                    ts = d["timestamp1"] or d["timestamp2"] or ""
                    level = d["level"] or "INFO"
                    msg = d["message"] or line_str
                    records.append({
                        "line_number": count,
                        "raw_timestamp": ts,
                        "level": level,
                        "message": msg,
                        "raw_text": line_str
                    })
                else:
                    records.append({
                        "line_number": count,
                        "raw_timestamp": "",
                        "level": "INFO",
                        "message": line_str,
                        "raw_text": line_str
                    })
            else:
                break
        return records
