import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent
CHROMA_PERSIST_DIR = BASE_DIR / "chroma_data"

# Ensure directories exist
CHROMA_PERSIST_DIR.mkdir(exist_ok=True)

# ChromaDB settings
CHROMA_COLLECTION_NAME = "regulatory_docs"
CHROMA_SIMILARITY_TOP_K = 8

# Gemini settings
GEMINI_MODEL = "gemini-3-flash-preview"  # or "models/gemini-1.5-pro"
GEMINI_TEMPERATURE = 0.1  # Low temperature for factual responses
GEMINI_MAX_TOKENS = 2048

# Retrieval settings
MIN_RETRIEVAL_CHUNKS = 3
MAX_RETRIEVAL_CHUNKS = 15
SECTION_WEIGHTS = {
    "indications": 1.0,
    "warnings": 1.2,  # Higher weight for safety info
    "adverse": 1.1,
    "contradictions": 1.3,  # Highest weight for contraindications
    "dosage": 0.8
}

# Confidence thresholds
CONFIDENCE_THRESHOLDS = {
    "high": 0.8,
    "medium": 0.6,
    "low": 0.4
}

# Logging
LOG_LEVEL = "INFO"