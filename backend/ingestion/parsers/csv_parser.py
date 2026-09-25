"""
CSV parser for metrics, logs, and ticket exports.
"""
import csv
import io
from typing import List, Dict, Any

class CSVParser:
    @staticmethod
    def parse(content: str, max_records: int = 5000) -> List[Dict[str, Any]]:
        # Fast streaming parse with memory protection for 1,000,000+ rows
        reader = csv.DictReader(io.StringIO(content))
        records = []
        for idx, row in enumerate(reader):
            if idx >= max_records:
                break
            records.append(dict(row))
        return records
