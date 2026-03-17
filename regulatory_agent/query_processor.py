import re
import logging
from typing import List, Dict, Optional
from models import RegulatoryQuery

logger = logging.getLogger(__name__)


class QueryProcessor:
    """
    Transforms raw molecule input into retrieval-ready queries.
    Handles drug name normalization and query expansion.
    """
    
    # Common drug name mappings
    DRUG_SYNONYMS = {
        "aspirin": ["acetylsalicylic acid", "asa", "2-acetoxybenzoic acid"],
        "paracetamol": ["acetaminophen", "apap", "n-acetyl-p-aminophenol"],
        "ibuprofen": ["brufen", "motrin", "advil"],
        "metformin": ["dimethylbiguanide", "glucophage"],
        "atorvastatin": ["lipitor"],
        "omeprazole": ["prilosec"],
        "amoxicillin": ["amoxil", "trimox"],
        "lisinopril": ["prinivil", "zestril"],
        "levothyroxine": ["synthroid", "levoxyl"],
        "amlodipine": ["norvasc"],
    }
    
    # Query templates for different regulatory aspects
    QUERY_TEMPLATES = [
        "{drug} label fda",
        "{drug} approved indications",
        "{drug} warnings precautions",
        "{drug} adverse reactions",
        "{drug} contraindications",
        "{drug} drug monograph",
        "{drug} prescribing information",
        "{drug} safety profile",
    ]
    
    def __init__(self, enable_expansion: bool = True):
        self.enable_expansion = enable_expansion
        logger.info("QueryProcessor initialized")
    
    def normalize_drug_name(self, raw_name: str) -> str:
        """
        Normalize drug name to canonical form.
        e.g., "Aspirin" -> "acetylsalicylic acid"
        """
        name = raw_name.lower().strip()
        
        # Check synonyms (reverse lookup - find canonical from synonym)
        for canonical, synonyms in self.DRUG_SYNONYMS.items():
            if name == canonical or name in synonyms:
                logger.debug(f"Normalized '{raw_name}' to '{canonical}'")
                return canonical
        
        # If no mapping found, return original (lowercased)
        logger.debug(f"No normalization for '{raw_name}', using as-is")
        return name
    
    def extract_alternative_names(self, drug_name: str) -> List[str]:
        """Get alternative names for a drug"""
        drug_lower = drug_name.lower()
        
        # Direct lookup
        if drug_lower in self.DRUG_SYNONYMS:
            return [drug_lower] + self.DRUG_SYNONYMS[drug_lower]
        
        # Check if it's a synonym of something
        for canonical, synonyms in self.DRUG_SYNONYMS.items():
            if drug_lower in synonyms:
                return [canonical] + synonyms
        
        return [drug_lower]
    
    def expand_queries(self, drug_name: str) -> List[str]:
        """
        Generate multiple search queries for better retrieval coverage.
        """
        expanded = []
        alt_names = self.extract_alternative_names(drug_name)
        
        for name in alt_names:
            for template in self.QUERY_TEMPLATES:
                query = template.format(drug=name)
                expanded.append(query)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for q in expanded:
            if q not in seen:
                seen.add(q)
                unique_queries.append(q)
        
        logger.info(f"Expanded '{drug_name}' to {len(unique_queries)} queries")
        return unique_queries[:10]  # Limit to top 10
    
    def process(self, molecule: str) -> RegulatoryQuery:
        """
        Main entry point - process raw molecule input.
        """
        normalized = self.normalize_drug_name(molecule)
        
        if self.enable_expansion:
            expanded = self.expand_queries(normalized)
        else:
            expanded = [normalized]
        
        query = RegulatoryQuery(
            molecule=normalized,
            expanded_queries=expanded,
            original_query=molecule
        )
        
        logger.info(f"Processed query: {query}")
        return query


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    processor = QueryProcessor()
    
    # Test cases
    for test in ["Aspirin", "Paracetamol", "Lipitor", "UnknownDrug"]:
        result = processor.process(test)
        print(f"\n{test} -> {result.molecule}")
        print(f"Expanded: {result.expanded_queries[:3]}...")