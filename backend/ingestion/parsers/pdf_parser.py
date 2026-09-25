"""
PDF Parser for architectural diagrams and historical post-mortems.
"""
from typing import List, Dict, Any

class PDFParser:
    @staticmethod
    def parse(file_bytes: bytes) -> List[Dict[str, Any]]:
        # Attempt to read PDF via pypdf or PyPDF2 if available, else extract textual ascii strings
        try:
            import pypdf
            import io
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            pages = []
            for idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                pages.append({"page_number": idx + 1, "text": text})
            return pages
        except Exception:
            # Fallback basic text extraction for raw text or formatted PDF stream
            try:
                decoded = file_bytes.decode("utf-8", errors="ignore")
                return [{"page_number": 1, "text": decoded}]
            except Exception as e:
                return [{"page_number": 1, "text": f"[Error reading PDF: {str(e)}]"}]
