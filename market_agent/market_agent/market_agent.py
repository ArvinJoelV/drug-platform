"""High-level agent wrapper for the market intelligence prototype."""

from __future__ import annotations

from typing import Any

from market_agent.rag_pipeline import MarketRAGPipeline


class MarketIntelligenceAgent:
    """Convenience wrapper around the naive RAG pipeline."""

    def __init__(
        self,
        persist_directory: str = "./chroma_store",
        collection_name: str = "market_intelligence",
        embedding_model_name: str = "all-MiniLM-L6-v2",
        top_k: int = 5,
    ) -> None:
        self.pipeline = MarketRAGPipeline(
            persist_directory=persist_directory,
            collection_name=collection_name,
            embedding_model_name=embedding_model_name,
            top_k=top_k,
        )

    def analyze_disease(
        self,
        disease_name: str,
        prevalence_csv_path: str | None = None,
        model: str = "gpt-4o-mini",
    ) -> dict[str, Any]:
        return self.pipeline.run(
            disease_name=disease_name,
            prevalence_csv_path=prevalence_csv_path,
            model=model,
        )
