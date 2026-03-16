"""ChromaDB helpers for indexing and retrieving text chunks."""

from __future__ import annotations

import math
from typing import Any

try:
    import chromadb
    from chromadb.errors import InvalidCollectionException
except ImportError:
    chromadb = None
    InvalidCollectionException = Exception


class MarketVectorStore:
    """Persist embeddings in ChromaDB and support similarity search."""

    def __init__(
        self,
        persist_directory: str = "./chroma_store",
        collection_name: str = "market_intelligence",
    ) -> None:
        self.collection_name = collection_name
        self._memory_items: list[dict[str, Any]] = []

        if chromadb is not None:
            self.client = chromadb.PersistentClient(path=persist_directory)
            self.collection = self.client.get_or_create_collection(name=collection_name)
        else:
            self.client = None
            self.collection = None

    def reset(self) -> None:
        """Delete and recreate the collection to keep prototype runs isolated."""
        if self.client is None:
            self._memory_items = []
            return

        collection_name = self.collection.name
        try:
            self.client.delete_collection(collection_name)
        except InvalidCollectionException:
            pass
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_documents(
        self,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        if self.collection is None:
            self._memory_items.extend(
                {
                    "id": item_id,
                    "document": text,
                    "embedding": embedding,
                    "metadata": metadata,
                }
                for item_id, text, embedding, metadata in zip(ids, texts, embeddings, metadatas)
            )
            return

        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def similarity_search(self, query_embedding: list[float], top_k: int = 5) -> dict[str, Any]:
        if self.collection is None:
            ranked = sorted(
                self._memory_items,
                key=lambda item: self._cosine_similarity(query_embedding, item["embedding"]),
                reverse=True,
            )[:top_k]
            return {
                "ids": [[item["id"] for item in ranked]],
                "documents": [[item["document"] for item in ranked]],
                "metadatas": [[item["metadata"] for item in ranked]],
            }

        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        numerator = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left)) or 1.0
        right_norm = math.sqrt(sum(b * b for b in right)) or 1.0
        return numerator / (left_norm * right_norm)

