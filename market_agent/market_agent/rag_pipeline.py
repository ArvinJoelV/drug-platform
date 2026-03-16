"""Naive RAG pipeline for market intelligence generation."""

from __future__ import annotations

import json
import os
from typing import Any

from market_agent.data_sources import build_documents
from market_agent.embeddings import EmbeddingModel
from market_agent.vector_store import MarketVectorStore

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except ImportError:
    class RecursiveCharacterTextSplitter:
        """Small fallback splitter so the prototype works without LangChain."""

        def __init__(self, chunk_size: int = 400, chunk_overlap: int = 60) -> None:
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap

        def split_text(self, text: str) -> list[str]:
            if not text:
                return []

            chunks: list[str] = []
            start = 0
            text_length = len(text)

            while start < text_length:
                end = min(start + self.chunk_size, text_length)
                chunks.append(text[start:end].strip())
                if end >= text_length:
                    break
                start = max(end - self.chunk_overlap, start + 1)

            return [chunk for chunk in chunks if chunk]


class MarketRAGPipeline:
    """End-to-end pipeline: fetch data, chunk, embed, retrieve, and summarize."""

    def __init__(
        self,
        persist_directory: str = "./chroma_store",
        collection_name: str = "market_intelligence",
        embedding_model_name: str = "all-MiniLM-L6-v2",
        top_k: int = 5,
    ) -> None:
        self.top_k = top_k
        self.embedding_model = EmbeddingModel(model_name=embedding_model_name)
        self.vector_store = MarketVectorStore(
            persist_directory=persist_directory,
            collection_name=collection_name,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=60,
        )

    def ingest(
        self,
        disease_name: str,
        prevalence_csv_path: str | None = None,
    ) -> list[dict[str, Any]]:
        """Collect source data and index chunked text into ChromaDB."""
        documents = build_documents(
            disease_name=disease_name,
            prevalence_csv_path=prevalence_csv_path,
        )

        chunked_documents: list[dict[str, Any]] = []
        for document in documents:
            chunks = self.text_splitter.split_text(document["text"])
            for chunk_index, chunk in enumerate(chunks):
                chunked_documents.append(
                    {
                        "id": f"{document['id']}-chunk-{chunk_index}",
                        "text": chunk,
                        "metadata": document["metadata"],
                    }
                )

        self.vector_store.reset()

        texts = [document["text"] for document in chunked_documents]
        embeddings = self.embedding_model.embed_documents(texts)
        self.vector_store.add_documents(
            ids=[document["id"] for document in chunked_documents],
            texts=texts,
            embeddings=embeddings,
            metadatas=[document["metadata"] for document in chunked_documents],
        )
        return chunked_documents

    def retrieve(self, disease_name: str) -> list[dict[str, Any]]:
        """Retrieve the most relevant chunks for the disease query."""
        query = (
            f"{disease_name} epidemiology prevalence incidence "
            "healthcare spending treatment market opportunity"
        )
        query_embedding = self.embedding_model.embed_query(query)
        results = self.vector_store.similarity_search(query_embedding=query_embedding, top_k=self.top_k)

        retrieved_chunks: list[dict[str, Any]] = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        ids = results.get("ids", [[]])[0]

        for chunk_id, text, metadata in zip(ids, documents, metadatas):
            retrieved_chunks.append(
                {
                    "id": chunk_id,
                    "text": text,
                    "metadata": metadata,
                }
            )

        return retrieved_chunks

    def build_prompt(self, disease_name: str, retrieved_chunks: list[dict[str, Any]]) -> str:
        """Create the RAG prompt that the LLM or fallback summarizer will use."""
        context = "\n".join(
            f"- {chunk['text']}"
            for chunk in retrieved_chunks
        )

        return f"""
You are a pharmaceutical market research analyst.
Using the following epidemiology and healthcare data,
generate a short market opportunity analysis.

Disease: {disease_name}

Context:
{context}

Return JSON with this schema:
{{
  "disease": "{disease_name}",
  "market_summary": "short paragraph",
  "key_statistics": ["stat 1", "stat 2", "stat 3"],
  "sources": ["source 1", "source 2"]
}}

Focus on:
- disease burden
- prevalence or epidemiology signals
- healthcare spending trends
- potential treatment market opportunity
""".strip()

    def generate_summary(
        self,
        disease_name: str,
        retrieved_chunks: list[dict[str, Any]],
        model: str = "gpt-4o-mini",
    ) -> dict[str, Any]:
        """Generate the final structured result with OpenAI or a local fallback."""
        prompt = self.build_prompt(disease_name, retrieved_chunks)

        if os.getenv("OPENAI_API_KEY"):
            try:
                from openai import OpenAI

                client = OpenAI()
                response = client.responses.create(model=model, input=prompt)
                output_text = getattr(response, "output_text", "").strip()
                if output_text:
                    return json.loads(output_text)
            except Exception:
                pass

        return self._fallback_summary(disease_name, retrieved_chunks)

    def _fallback_summary(
        self,
        disease_name: str,
        retrieved_chunks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Simple summary for local/offline execution during a hackathon demo."""
        sources = sorted(
            {
                chunk["metadata"].get("source", "Unknown source")
                for chunk in retrieved_chunks
            }
        )
        key_statistics = [
            chunk["text"]
            for chunk in retrieved_chunks[:3]
        ]

        market_summary = (
            f"{disease_name} shows relevant disease-burden and health-system signals in the retrieved data. "
            "Healthcare expenditure indicators from WHO and World Bank suggest where payer capacity may support "
            "new therapies, while any disease-specific prevalence rows highlight the potential patient pool. "
            "Taken together, these signals can be used as an early proxy for treatment market attractiveness."
        )

        return {
            "disease": disease_name,
            "market_summary": market_summary,
            "key_statistics": key_statistics,
            "sources": sources,
        }

    def run(
        self,
        disease_name: str,
        prevalence_csv_path: str | None = None,
        model: str = "gpt-4o-mini",
    ) -> dict[str, Any]:
        """Run the full naive RAG pipeline."""
        self.ingest(disease_name=disease_name, prevalence_csv_path=prevalence_csv_path)
        retrieved_chunks = self.retrieve(disease_name=disease_name)
        return self.generate_summary(
            disease_name=disease_name,
            retrieved_chunks=retrieved_chunks,
            model=model,
        )

