import logging
from typing import List, Dict, Any
from models import RetrievedChunk, RegulatorySection

logger = logging.getLogger(__name__)


class ContextBuilder:
    """
    Builds structured context from retrieved chunks for LLM consumption.
    Organizes by regulatory section and ensures clean formatting.
    """
    
    def __init__(self, max_chunks_per_section: int = 5):
        self.max_chunks_per_section = max_chunks_per_section
        logger.info("ContextBuilder initialized")
    
    def build_context(self, chunks: List[RetrievedChunk]) -> str:
        """
        Convert retrieved chunks into a clean, structured context string.
        """
        # Group chunks by section
        sections = self._group_by_section(chunks)
        
        # Build context sections
        context_parts = []
        
        # Add metadata summary first
        context_parts.append(self._build_metadata_summary(chunks))
        
        # Add each regulatory section
        for section in RegulatorySection:
            if section in sections:
                section_text = self._format_section(section, sections[section])
                context_parts.append(section_text)
        
        # Add source references
        context_parts.append(self._build_sources_section(chunks))
        
        # Join everything
        full_context = "\n\n".join(context_parts)
        
        logger.debug(f"Built context with {len(full_context)} characters")
        return full_context
    
    def _group_by_section(self, chunks: List[RetrievedChunk]) -> Dict[RegulatorySection, List[RetrievedChunk]]:
        """Group chunks by regulatory section"""
        sections = {}
        
        for chunk in chunks:
            if chunk.section not in sections:
                sections[chunk.section] = []
            
            # Limit chunks per section
            if len(sections[chunk.section]) < self.max_chunks_per_section:
                sections[chunk.section].append(chunk)
        
        return sections
    
    def _format_section(self, section: RegulatorySection, chunks: List[RetrievedChunk]) -> str:
        """Format a single regulatory section"""
        header = f"[{section.value.upper()}]"
        lines = [header]
        
        # Sort chunks by score
        sorted_chunks = sorted(chunks, key=lambda x: x.score, reverse=True)
        
        for i, chunk in enumerate(sorted_chunks, 1):
            # Add a clean bullet point
            lines.append(f"• {chunk.content.strip()}")
        
        return "\n".join(lines)
    
    def _build_metadata_summary(self, chunks: List[RetrievedChunk]) -> str:
        """Create a summary of the retrieval metadata"""
        drugs = set(ch.drug_name for ch in chunks)
        sections = set(ch.section.value for ch in chunks)
        sources = set(ch.source for ch in chunks)
        
        summary = [
            "[RETRIEVAL METADATA]",
            f"Drug names found: {', '.join(sorted(drugs))}",
            f"Sections covered: {', '.join(sorted(sections))}",
            f"Sources: {', '.join(sorted(sources))}",
            f"Total relevant chunks: {len(chunks)}"
        ]
        
        return "\n".join(summary)
    
    def _build_sources_section(self, chunks: List[RetrievedChunk]) -> str:
        """List all unique sources"""
        sources = sorted(set(ch.source for ch in chunks))
        
        lines = ["[SOURCES]"]
        for source in sources:
            lines.append(f"• {source}")
        
        return "\n".join(lines)
    
    def build_structured_context(self, chunks: List[RetrievedChunk]) -> Dict[str, Any]:
        """
        Alternative: Build a structured dictionary instead of a string.
        Useful if you want to pass structured data to the LLM.
        """
        sections = self._group_by_section(chunks)
        
        structured = {
            "metadata": {
                "drugs": list(set(ch.drug_name for ch in chunks)),
                "total_chunks": len(chunks),
                "sections_covered": list(sections.keys())
            },
            "regulatory_data": {},
            "sources": list(set(ch.source for ch in chunks))
        }
        
        for section, section_chunks in sections.items():
            structured["regulatory_data"][section.value] = [
                {
                    "content": ch.content,
                    "source": ch.source,
                    "confidence": ch.score
                }
                for ch in sorted(section_chunks, key=lambda x: x.score, reverse=True)
            ]
        
        return structured
    
    def extract_key_facts(self, chunks: List[RetrievedChunk]) -> Dict[str, List[str]]:
        """
        Extract key facts by section (simplified extraction).
        This is a fallback if LLM is not available.
        """
        facts = {
            "indications": [],
            "warnings": [],
            "contradictions": [],
            "adverse": []
        }
        
        for chunk in chunks:
            # Simple extraction - split by sentences and take key ones
            sentences = chunk.content.split('.')
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 20:  # Only substantial sentences
                    if chunk.section.value in facts:
                        facts[chunk.section.value].append(sentence)
        
        # Deduplicate and limit
        for key in facts:
            seen = set()
            unique = []
            for item in facts[key]:
                if item not in seen and len(seen) < 5:
                    seen.add(item)
                    unique.append(item)
            facts[key] = unique
        
        return facts


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    from chroma_client import ChromaRegulatoryClient
    from query_processor import QueryProcessor
    from retriever import RegulatoryRetriever
    from data_loader import RegulatoryDataLoader
    
    # Setup
    client = ChromaRegulatoryClient()
    loader = RegulatoryDataLoader(client)
    loader.load_sample_data()
    
    retriever = RegulatoryRetriever(client)
    processor = QueryProcessor()
    builder = ContextBuilder()
    
    # Test
    query = processor.process("Aspirin")
    chunks = retriever.retrieve(query)
    
    context = builder.build_context(chunks)
    print("\n" + "="*50)
    print("BUILT CONTEXT:")
    print("="*50)
    print(context)
    
    # Structured version
    structured = builder.build_structured_context(chunks)
    print("\n" + "="*50)
    print("STRUCTURED CONTEXT:")
    print("="*50)
    for section, data in structured["regulatory_data"].items():
        print(f"\n{section.upper()}: {len(data)} items")