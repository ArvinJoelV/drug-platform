"""Embedding utilities for the Market Intelligence Agent prototype."""

from __future__ import annotations

import math

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


class EmbeddingModel:
    """Thin wrapper around sentence-transformers for clearer usage."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self.model = SentenceTransformer(model_name) if SentenceTransformer else None

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if self.model is not None:
            return self.model.encode(texts, convert_to_numpy=True).tolist()
        return [self._fallback_embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        if self.model is not None:
            return self.model.encode(text, convert_to_numpy=True).tolist()
        return self._fallback_embed(text)

    def _fallback_embed(self, text: str, dimensions: int = 128) -> list[float]:
        """Cheap hashing-based embedding for environments without sentence-transformers."""
        vector = [0.0] * dimensions
        tokens = text.lower().split()
        if not tokens:
            return vector

        for token in tokens:
            slot = hash(token) % dimensions
            vector[slot] += 1.0

        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

