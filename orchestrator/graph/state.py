from typing import Dict, Any, Optional, Annotated
from typing_extensions import TypedDict
import operator

def merge_dict(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    if a is None:
        a = {}
    if b is None:
        b = {}
    res = a.copy()
    res.update(b)
    return res

class OrchestratorState(TypedDict):
    """
    Shared state for the Orchestrator LangGraph execution.
    """
    molecule: str
    analysis_id: Optional[str]
    
    # Store data from each agent
    clinical_data: Optional[Dict[str, Any]]
    literature_data: Optional[Dict[str, Any]]
    patent_data: Optional[Dict[str, Any]]
    regulatory_data: Optional[Dict[str, Any]]
    market_data: Optional[Dict[str, Any]]
    
    # Unified and derived outputs
    aggregated_report: Optional[Dict[str, Any]]
    intelligence_data: Optional[Dict[str, Any]]
    regulatory_postcheck: Optional[Dict[str, Any]]
    llm_report: Optional[Dict[str, Any]]
    
    # Final deterministic output
    final_report: Optional[Dict[str, Any]]
    
    # Dictionary of errors encountered by each node
    # Annotated with a merge function to allow parallel nodes to update safely
    errors: Annotated[Dict[str, str], merge_dict]
    
    # Node status details 
    status: Annotated[Dict[str, str], merge_dict]
