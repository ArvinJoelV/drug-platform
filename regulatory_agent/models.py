from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class RegulatorySection(str, Enum):
    INDICATIONS = "indications"
    WARNINGS = "warnings"
    ADVERSE = "adverse"
    CONTRADICTIONS = "contradictions"
    DOSAGE = "dosage"


class RegulatoryDocument(BaseModel):
    """Model for regulatory documents stored in ChromaDB"""
    drug_name: str
    section: RegulatorySection
    content: str
    source: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class RegulatoryQuery(BaseModel):
    """Normalized query for retrieval"""
    molecule: str
    expanded_queries: List[str] = Field(default_factory=list)
    original_query: str


class RetrievedChunk(BaseModel):
    """Chunk retrieved from ChromaDB"""
    content: str
    drug_name: str
    section: RegulatorySection
    source: str
    score: float
    metadata: Optional[Dict[str, Any]] = None


class RegulatoryIntelligence(BaseModel):
    """Final output structure"""
    drug: str
    approved_indications: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
    adverse_events: List[str] = Field(default_factory=list)
    regulatory_summary: str = ""
    confidence: float = 0.0
    sources: List[str] = Field(default_factory=list)
    retrieval_metadata: Optional[Dict[str, Any]] = None


class AgentRequest(BaseModel):
    """Input request format"""
    molecule: str


class AgentResponse(BaseModel):
    """Output response format"""
    success: bool
    data: Optional[RegulatoryIntelligence] = None
    error: Optional[str] = None