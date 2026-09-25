"""
Unified File & Stream Ingestion Gateway.
Accepts raw uploads or API payloads, calculates SHA-256 hash for auditability,
detects the source format, and delegates to the appropriate parser.
"""
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List
from backend.ingestion.source_detector import SourceDetector
from backend.ingestion.parsers.json_parser import JSONParser
from backend.ingestion.parsers.csv_parser import CSVParser
from backend.ingestion.parsers.log_parser import LogParser
from backend.ingestion.parsers.markdown_parser import MarkdownParser
from backend.ingestion.parsers.pdf_parser import PDFParser

class IngestionResult:
    def __init__(
        self,
        source_id: str,
        filename: str,
        source_type: str,
        content_hash: str,
        raw_content: str,
        records: List[Dict[str, Any]],
        ingested_at: str,
        total_records_count: int = 0
    ):
        self.source_id = source_id
        self.filename = filename
        self.source_type = source_type
        self.content_hash = content_hash
        self.raw_content = raw_content
        self.records = records
        self.ingested_at = ingested_at
        self.total_records_count = total_records_count if total_records_count > 0 else len(records)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "filename": self.filename,
            "source_type": self.source_type,
            "content_hash": self.content_hash,
            "records_count": self.total_records_count,
            "ingested_at": self.ingested_at
        }

class FileIngestor:
    @staticmethod
    def ingest(content: str, filename: str = "upload.txt", source_id: str = "") -> IngestionResult:
        if not source_id:
            source_id = f"src_{hashlib.md5(filename.encode()).hexdigest()[:8]}"
            
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        source_type = SourceDetector.detect(content, filename)
        ingested_at = datetime.now(timezone.utc).isoformat()
        
        records = []
        lower_name = filename.lower()
        total_count = 0

        # Exact, accurate dataset event count
        lines = [l for l in content.splitlines() if l.strip()]
        line_count = len(lines)

        if lower_name.endswith(".json") or (content.strip().startswith("{") or content.strip().startswith("[")):
            try:
                records = JSONParser.parse(content)
                total_count = len(records)
            except Exception:
                records = LogParser.parse(content, max_records=5000)
                total_count = line_count
        elif lower_name.endswith(".csv"):
            try:
                records = CSVParser.parse(content, max_records=5000)
                total_count = max(0, line_count - 1)  # exact data rows excluding header
            except Exception:
                records = LogParser.parse(content, max_records=5000)
                total_count = max(0, line_count - 1)
        elif lower_name.endswith(".md"):
            records = MarkdownParser.parse(content)
            total_count = len(records)
        elif lower_name.endswith(".pdf"):
            records = PDFParser.parse(content.encode("utf-8", errors="ignore"))
            total_count = len(records)
        else:
            records = LogParser.parse(content, max_records=5000)
            total_count = line_count

        return IngestionResult(
            source_id=source_id,
            filename=filename,
            source_type=source_type,
            content_hash=content_hash,
            raw_content=content,
            records=records,
            ingested_at=ingested_at,
            total_records_count=total_count
        )
