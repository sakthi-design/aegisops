"""
Markdown and text parser for runbooks, postmortems, and release notes.
"""
from typing import List, Dict, Any

class MarkdownParser:
    @staticmethod
    def parse(content: str) -> List[Dict[str, Any]]:
        sections = []
        current_header = "Introduction"
        current_lines = []

        for line in content.splitlines():
            if line.startswith("#"):
                if current_lines:
                    sections.append({
                        "section_title": current_header,
                        "text": "\n".join(current_lines).strip()
                    })
                    current_lines = []
                current_header = line.lstrip("#").strip()
            else:
                current_lines.append(line)

        if current_lines:
            sections.append({
                "section_title": current_header,
                "text": "\n".join(current_lines).strip()
            })

        return sections if sections else [{"section_title": "Full Document", "text": content.strip()}]
