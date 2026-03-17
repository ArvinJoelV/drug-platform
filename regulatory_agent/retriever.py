import logging
from typing import List, Dict, Any, Optional
from chroma_client import ChromaRegulatoryClient
from models import RetrievedChunk, RegulatorySection, RegulatoryQuery
from config import CHROMA_SIMILARITY_TOP_K, SECTION_WEIGHTS

logger = logging.getLogger(__name__)


class RegulatoryRetriever:
    """
    Naive RAG retriever that fetches relevant regulatory chunks from ChromaDB.
    """
    
    def __init__(self, chroma_client: ChromaRegulatoryClient):
        self.chroma_client = chroma_client
        logger.info("RegulatoryRetriever initialized")
    
    def retrieve(self, query: RegulatoryQuery, top_k: int = None) -> List[RetrievedChunk]:
        """
        Main retrieval method - fetches chunks for all expanded queries.
        """
        if top_k is None:
            top_k = CHROMA_SIMILARITY_TOP_K
        
        all_results = []
        seen_contents = set()
        
        # Search with each expanded query
        for q in query.expanded_queries:
            results = self.chroma_client.search(q, n_results=top_k)
            
            for result in results:
                # Deduplicate by content
                content_preview = result['document'][:200]  # Use preview for dedup
                if content_preview in seen_contents:
                    continue
                seen_contents.add(content_preview)
                
                # Parse section from metadata
                section_str = result['metadata'].get('section', 'unknown')
                try:
                    section = RegulatorySection(section_str)
                except ValueError:
                    logger.warning(f"Unknown section: {section_str}, defaulting to warnings")
                    section = RegulatorySection.WARNINGS
                
                chunk = RetrievedChunk(
                    content=result['document'],
                    drug_name=result['metadata'].get('drug_name', 'unknown'),
                    section=section,
                    source=result['metadata'].get('source', 'unknown'),
                    score=1.0 - result.get('distance', 0),  # Convert distance to similarity
                    metadata=result['metadata']
                )
                all_results.append(chunk)
        
        # Remove duplicates more thoroughly and sort by score
        unique_chunks = self._deduplicate_chunks(all_results)
        unique_chunks.sort(key=lambda x: x.score, reverse=True)
        
        # Apply section weighting (optional - can boost certain sections)
        weighted_chunks = self._apply_section_weights(unique_chunks)
        weighted_chunks.sort(key=lambda x: x.score, reverse=True)
        
        # Limit to top_k
        final_chunks = weighted_chunks[:top_k]
        
        logger.info(f"Retrieved {len(final_chunks)} unique chunks for '{query.molecule}'")
        return final_chunks
    
    def _deduplicate_chunks(self, chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        """
        Remove near-duplicate chunks.
        """
        unique = []
        seen = set()
        
        for chunk in chunks:
            # Create a fingerprint (simplified - in production use proper dedup)
            fingerprint = f"{chunk.drug_name}_{chunk.section}_{chunk.content[:100]}"
            
            if fingerprint not in seen:
                seen.add(fingerprint)
                unique.append(chunk)
        
        return unique
    
    def _apply_section_weights(self, chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        """
        Apply different weights to different regulatory sections.
        This helps prioritize safety-critical information.
        """
        weighted_chunks = []
        
        for chunk in chunks:
            # Create a copy with adjusted score
            weight = SECTION_WEIGHTS.get(chunk.section.value, 1.0)
            weighted_chunk = RetrievedChunk(
                content=chunk.content,
                drug_name=chunk.drug_name,
                section=chunk.section,
                source=chunk.source,
                score=chunk.score * weight,  # Apply weight
                metadata=chunk.metadata
            )
            weighted_chunks.append(weighted_chunk)
        
        return weighted_chunks
    
    def retrieve_by_drug(self, drug_name: str, section: Optional[str] = None) -> List[RetrievedChunk]:
        """
        Direct retrieval by drug name (bypasses query expansion).
        Useful for testing or when you know exactly what you want.
        """
        results = self.chroma_client.search_by_drug(drug_name, section)
        
        chunks = []
        for result in results:
            section_str = result['metadata'].get('section', 'unknown')
            try:
                section = RegulatorySection(section_str)
            except ValueError:
                section = RegulatorySection.WARNINGS
            
            chunk = RetrievedChunk(
                content=result['document'],
                drug_name=result['metadata'].get('drug_name', 'unknown'),
                section=section,
                source=result['metadata'].get('source', 'unknown'),
                score=1.0 - result.get('distance', 0),
                metadata=result['metadata']
            )
            chunks.append(chunk)
        
        return chunks
    
    def get_retrieval_stats(self, chunks: List[RetrievedChunk]) -> Dict[str, Any]:
        """
        Generate statistics about retrieved chunks.
        Used for confidence scoring.
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "sections_found": [],
                "avg_score": 0,
                "unique_sources": 0
            }
        
        sections = set(ch.section.value for ch in chunks)
        sources = set(ch.source for ch in chunks)
        avg_score = sum(ch.score for ch in chunks) / len(chunks)
        
        return {
            "total_chunks": len(chunks),
            "sections_found": list(sections),
            "section_coverage": len(sections),
            "avg_score": avg_score,
            "unique_sources": len(sources),
            "sources": list(sources)
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    from query_processor import QueryProcessor
    
    # Setup
    client = ChromaRegulatoryClient()
    retriever = RegulatoryRetriever(client)
    processor = QueryProcessor()
    
    # Test
    query = processor.process("Aspirin")
    chunks = retriever.retrieve(query)
    
    print(f"\nRetrieved {len(chunks)} chunks for Aspirin:")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n{i+1}. [{chunk.section.value}] Score: {chunk.score:.2f}")
        print(f"   {chunk.content[:150]}...")
    
    print(f"\nStats: {retriever.get_retrieval_stats(chunks)}")