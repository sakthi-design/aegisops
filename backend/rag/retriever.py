"""
Knowledge Base Loader and High-Level Retriever.
Loads operational runbooks, architecture topology, and SRE policies from data/knowledge_base.
"""
import os
from pathlib import Path
from typing import List, Dict, Any
from backend.rag.embeddings import TextEmbedder
from backend.rag.vector_store import VectorStore
from backend.rag.hybrid_search import HybridRetriever

class KnowledgeRetriever:
    _instance = None

    def __init__(self, kb_dir: str = "data/knowledge_base"):
        self.kb_dir = Path(kb_dir)
        self.embedder = TextEmbedder()
        self.vector_store = VectorStore()
        self.retriever = HybridRetriever(self.embedder, self.vector_store)
        self.is_indexed = False
        self._query_cache: Dict[str, List[Dict[str, Any]]] = {}

    @classmethod
    def get_instance(cls, kb_dir: str = "data/knowledge_base") -> "KnowledgeRetriever":
        if cls._instance is None:
            cls._instance = cls(kb_dir=kb_dir)
            cls._instance.initialize_and_index()
        return cls._instance

    def initialize_and_index(self):
        chunks: List[Dict[str, Any]] = []
        if not self.kb_dir.exists():
            return

        chunk_id = 1
        for md_file in self.kb_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8", errors="ignore")
                rel_path = str(md_file.relative_to(self.kb_dir))
                doc_type = md_file.parent.name
                
                # Split into markdown sections or paragraphs
                sections = content.split("\n## ")
                for sec in sections:
                    clean_text = sec.strip()
                    if len(clean_text) < 40:
                        continue
                    chunks.append({
                        "chunk_id": f"CHUNK-{chunk_id:04d}",
                        "source_file": rel_path,
                        "doc_type": doc_type,
                        "title": clean_text.splitlines()[0].replace("#", "").strip()[:80],
                        "text": clean_text[:1200]
                    })
                    chunk_id += 1
            except Exception as e:
                continue

        if chunks:
            self.retriever.index(chunks)
            self.is_indexed = True

    def retrieve_context(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        cache_key = f"{query.strip().lower()}_{top_k}"
        if cache_key in self._query_cache:
            return self._query_cache[cache_key]

        if not self.is_indexed:
            self.initialize_and_index()
        results = self.retriever.search(query, top_k=top_k)
        if len(self._query_cache) < 256:
            self._query_cache[cache_key] = results
        return results
