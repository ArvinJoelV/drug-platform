import logging
from typing import List, Dict, Any
from models import RetrievedChunk, RegulatoryIntelligence
from config import CONFIDENCE_THRESHOLDS

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """
    Calculates confidence scores for regulatory intelligence based on retrieval quality.
    Hybrid approach: combines retrieval stats with LLM output quality.
    """
    
    def __init__(self):
        self.thresholds = CONFIDENCE_THRESHOLDS
        logger.info("ConfidenceScorer initialized")
    
    def calculate(self, chunks: List[RetrievedChunk], 
                  intelligence: RegulatoryIntelligence) -> float:
        """
        Calculate overall confidence score (0.0 to 1.0).
        """
        if not chunks:
            return 0.0
        
        # Component scores
        retrieval_score = self._score_retrieval_quality(chunks)
        coverage_score = self._score_section_coverage(chunks)
        consistency_score = self._score_internal_consistency(chunks)
        output_score = self._score_output_quality(intelligence)
        
        # Weighted combination
        weights = {
            "retrieval": 0.3,
            "coverage": 0.3,
            "consistency": 0.2,
            "output": 0.2
        }
        
        final_score = (
            retrieval_score * weights["retrieval"] +
            coverage_score * weights["coverage"] +
            consistency_score * weights["consistency"] +
            output_score * weights["output"]
        )
        
        # Ensure score is in [0, 1]
        final_score = max(0.0, min(1.0, final_score))
        
        logger.debug(f"Confidence calculation: retrieval={retrieval_score:.2f}, "
                    f"coverage={coverage_score:.2f}, consistency={consistency_score:.2f}, "
                    f"output={output_score:.2f} -> final={final_score:.2f}")
        
        return final_score
    
    def _score_retrieval_quality(self, chunks: List[RetrievedChunk]) -> float:
        """Score based on number and quality of retrieved chunks"""
        if not chunks:
            return 0.0
        
        # Factor 1: Number of chunks (more is better, up to a point)
        chunk_count = len(chunks)
        count_score = min(1.0, chunk_count / 10)  # 10 chunks = perfect score
        
        # Factor 2: Average similarity score
        avg_score = sum(ch.score for ch in chunks) / len(chunks)
        
        # Factor 3: Diversity of sources
        unique_sources = len(set(ch.source for ch in chunks if ch.source))
        source_score = min(1.0, unique_sources / 3)  # 3 sources = perfect
        
        # Combine
        retrieval_score = (count_score * 0.3 + avg_score * 0.5 + source_score * 0.2)
        
        return retrieval_score
    
    def _score_section_coverage(self, chunks: List[RetrievedChunk]) -> float:
        """Score based on which regulatory sections are covered"""
        sections_found = set(ch.section for ch in chunks)
        
        # Important sections for repurposing decisions
        critical_sections = {"indications", "warnings", "contradictions"}
        important_sections = {"adverse", "dosage"}
        
        critical_covered = sum(1 for s in critical_sections if s in sections_found)
        important_covered = sum(1 for s in important_sections if s in sections_found)
        
        # Weight critical sections more heavily
        coverage_score = (
            (critical_covered / len(critical_sections)) * 0.7 +
            (important_covered / len(important_sections)) * 0.3
        )
        
        return coverage_score
    
    def _score_internal_consistency(self, chunks: List[RetrievedChunk]) -> float:
        """Score based on consistency across different chunks"""
        if len(chunks) < 2:
            return 0.5  # Neutral score for single chunk
        
        # Check for contradictions (simplified)
        # In production, you'd use more sophisticated contradiction detection
        
        # Group by section
        sections = {}
        for chunk in chunks:
            if chunk.section not in sections:
                sections[chunk.section] = []
            sections[chunk.section].append(chunk)
        
        # Check each section for major contradictions
        contradiction_count = 0
        total_comparisons = 0
        
        for section, section_chunks in sections.items():
            if len(section_chunks) > 1:
                # Compare first chunk with others
                base_content = section_chunks[0].content.lower()
                for other in section_chunks[1:]:
                    other_content = other.content.lower()
                    total_comparisons += 1
                    
                    # Simple check for negation (very basic)
                    if "not" in base_content and "not" not in other_content:
                        if any(word in other_content for word in ["contraindicated", "avoid", "do not use"]):
                            contradiction_count += 1
                    elif "contraindicated" in base_content and "indicated" in other_content:
                        contradiction_count += 1
        
        if total_comparisons == 0:
            return 0.7
        
        consistency_score = 1.0 - (contradiction_count / total_comparisons)
        return max(0.0, consistency_score)
    
    def _score_output_quality(self, intelligence: RegulatoryIntelligence) -> float:
        """Score based on the quality of the synthesized output"""
        score = 0.0
        total_weight = 0
        
        # Check if we have any indications
        if intelligence.approved_indications:
            score += min(1.0, len(intelligence.approved_indications) / 3) * 0.3
            total_weight += 0.3
        
        # Check warnings (safety critical)
        if intelligence.warnings:
            score += min(1.0, len(intelligence.warnings) / 3) * 0.3
            total_weight += 0.3
        
        # Check contraindications (very critical)
        if intelligence.contradictions:
            score += min(1.0, len(intelligence.contradictions) / 2) * 0.2
            total_weight += 0.2
        
        # Check if we have a meaningful summary
        if intelligence.regulatory_summary and len(intelligence.regulatory_summary) > 20:
            score += 0.2
            total_weight += 0.2
        
        if total_weight == 0:
            return 0.0
        
        return score / total_weight
    
    def get_confidence_level(self, score: float) -> str:
        """Convert numerical score to confidence level"""
        if score >= self.thresholds["high"]:
            return "HIGH"
        elif score >= self.thresholds["medium"]:
            return "MEDIUM"
        elif score >= self.thresholds["low"]:
            return "LOW"
        else:
            return "VERY LOW"
    
    def explain_score(self, chunks: List[RetrievedChunk], 
                      intelligence: RegulatoryIntelligence) -> Dict[str, Any]:
        """Generate explanation of confidence score components"""
        return {
            "overall_score": self.calculate(chunks, intelligence),
            "components": {
                "retrieval_quality": self._score_retrieval_quality(chunks),
                "section_coverage": self._score_section_coverage(chunks),
                "internal_consistency": self._score_internal_consistency(chunks),
                "output_quality": self._score_output_quality(intelligence)
            },
            "retrieval_stats": {
                "chunk_count": len(chunks),
                "unique_sources": len(set(ch.source for ch in chunks if ch.source)),
                "sections_covered": list(set(ch.section.value for ch in chunks))
            }
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    from models import RegulatorySection, RetrievedChunk
    
    # Create sample chunks
    chunks = [
        RetrievedChunk(
            content="Aspirin is indicated for pain relief",
            drug_name="aspirin",
            section=RegulatorySection.INDICATIONS,
            source="FDA Label",
            score=0.9
        ),
        RetrievedChunk(
            content="WARNING: Risk of bleeding",
            drug_name="aspirin",
            section=RegulatorySection.WARNINGS,
            source="FDA Label",
            score=0.85
        ),
        RetrievedChunk(
            content="Contraindicated in children with viral infections",
            drug_name="aspirin",
            section=RegulatorySection.CONTRADICTIONS,
            source="FDA Label",
            score=0.8
        )
    ]
    
    # Sample intelligence
    intelligence = RegulatoryIntelligence(
        drug="aspirin",
        approved_indications=["Pain relief", "Cardiovascular prevention"],
        warnings=["Risk of bleeding", "Reye's syndrome"],
        contradictions=["Children with viral infections"],
        adverse_events=["GI irritation"],
        regulatory_summary="Widely used NSAID with cardiovascular benefits but bleeding risks.",
        sources=["FDA Label"]
    )
    
    scorer = ConfidenceScorer()
    score = scorer.calculate(chunks, intelligence)
    level = scorer.get_confidence_level(score)
    
    print(f"Confidence Score: {score:.2f} ({level})")
    print("\nExplanation:")
    explanation = scorer.explain_score(chunks, intelligence)
    print(f"Components: {explanation['components']}")