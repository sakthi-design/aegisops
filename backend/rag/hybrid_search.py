"""
Hybrid Retrieval Engine: BM25 Lexical Matching + Dense Vector Search.
Uses Reciprocal Rank Fusion (RRF) to merge keyword and semantic signals.
"""
import math
import re
from typing import List, Dict, Any
from collections import Counter
import numpy as np
from backend.rag.embeddings import TextEmbedder
from backend.rag.vector_store import VectorStore

class BM25Searcher:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: List[List[str]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.df: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.n_docs = 0

    def fit(self, texts: List[str]):
        self.corpus = [self._tokenize(t) for t in texts]
        self.n_docs = len(self.corpus)
        if self.n_docs == 0:
            return
        self.doc_lengths = [len(doc) for doc in self.corpus]
        self.avg_doc_len = sum(self.doc_lengths) / self.n_docs

        for doc in self.corpus:
            unique_terms = set(doc)
            for t in unique_terms:
                self.df[t] = self.df.get(t, 0) + 1

        for term, freq in self.df.items():
            self.idf[term] = math.log(1.0 + (self.n_docs - freq + 0.5) / (freq + 0.5))

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", text.lower())

    def search(self, query: str, top_k: int = 10) -> List[int]:
        q_tokens = self._tokenize(query)
        scores = []
        for i, doc in enumerate(self.corpus):
            doc_len = self.doc_lengths[i]
            score = 0.0
            term_counts = Counter(doc)
            for qt in q_tokens:
                if qt in term_counts:
                    tf = term_counts[qt]
                    denom = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / (self.avg_doc_len or 1.0)))
                    score += self.idf.get(qt, 0.0) * ((tf * (self.k1 + 1.0)) / denom)
            scores.append((i, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return [idx for idx, s in scores[:top_k] if s > 0]

class HybridRetriever:
    def __init__(self, embedder: TextEmbedder, vector_store: VectorStore):
        self.embedder = embedder
        self.vector_store = vector_store
        self.bm25 = BM25Searcher()
        self.chunks: List[Dict[str, Any]] = []

    def index(self, chunks: List[Dict[str, Any]]):
        self.chunks = chunks
        texts = [c["text"] for c in chunks]
        self.bm25.fit(texts)
        embeddings = self.embedder.embed(texts)
        self.vector_store.add_documents(chunks, embeddings)

    def search(self, query: str, top_k: int = 4, rrf_k: int = 60) -> List[Dict[str, Any]]:
        if not self.chunks:
            return []

        # 1. BM25 Search
        bm25_indices = self.bm25.search(query, top_k=top_k * 2)

        # 2. Vector Search
        q_vec = self.embedder.embed([query])
        vec_results = self.vector_store.search(q_vec, top_k=top_k * 2)

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[int, float] = {}

        for rank, doc_idx in enumerate(bm25_indices):
            rrf_scores[doc_idx] = rrf_scores.get(doc_idx, 0.0) + (1.0 / (rrf_k + rank + 1))

        # Map vector results back to global chunk index
        for rank, item in enumerate(vec_results):
            # Locate index of chunk
            chunk_id = item.get("chunk_id")
            for idx, c in enumerate(self.chunks):
                if c.get("chunk_id") == chunk_id:
                    rrf_scores[idx] = rrf_scores.get(idx, 0.0) + (1.0 / (rrf_k + rank + 1))
                    break

        # Sort by merged RRF score
        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        final_results = []
        for idx, rrf_score in sorted_docs:
            res = self.chunks[idx].copy()
            res["rrf_score"] = float(rrf_score)
            final_results.append(res)

        return final_results
