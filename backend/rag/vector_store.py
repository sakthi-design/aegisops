"""
In-memory Vector Store for Knowledge Chunks with Cosine Similarity Search.
"""
import numpy as np
from typing import List, Dict, Any

class VectorStore:
    def __init__(self):
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings: np.ndarray = np.empty((0, 512))

    def add_documents(self, chunks: List[Dict[str, Any]], embeddings: np.ndarray):
        self.chunks.extend(chunks)
        if self.embeddings.shape[0] == 0:
            self.embeddings = embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, embeddings])

    def search(self, query_vec: np.ndarray, top_k: int = 4) -> List[Dict[str, Any]]:
        if len(self.chunks) == 0:
            return []
        
        # Cosine similarity (query_vec is 1 x D, embeddings is N x D)
        scores = np.dot(self.embeddings, query_vec.T).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            chunk = self.chunks[idx].copy()
            chunk["vector_score"] = float(scores[idx])
            results.append(chunk)
        return results
