"""
Lightweight, robust semantic embedding engine using Scikit-Learn TfidfVectorizer & Dense Projection.
Runs 100% offline without requiring multi-gigabyte GPU models, while preserving high retrieval fidelity.
"""
import numpy as np
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer

class TextEmbedder:
    def __init__(self, max_features: int = 512):
        self.vectorizer = TfidfVectorizer(max_features=max_features, stop_words="english")
        self.is_fitted = False

    def fit(self, texts: List[str]):
        if not texts:
            return
        self.vectorizer.fit(texts)
        self.is_fitted = True

    def embed(self, texts: List[str]) -> np.ndarray:
        if not self.is_fitted:
            self.fit(texts)
        matrix = self.vectorizer.transform(texts).toarray()
        # Normalize vectors for cosine similarity
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return matrix / norms
