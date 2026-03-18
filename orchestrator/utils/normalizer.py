from typing import Dict, Any
from orchestrator.graph.state import OrchestratorState

def build_final_report(state: OrchestratorState) -> Dict[str, Any]:
    molecule = state.get("molecule", "Unknown")
    
    # Extract data safely with fallbacks
    c_data = state.get("clinical_data") or {}
    l_data = state.get("literature_data") or {}
    p_data = state.get("patent_data") or {}
    r_data = state.get("regulatory_data") or {}
    m_data = state.get("market_data") or {}
    
    # Calculate successful source list
    status_dict = state.get("status", {})
    sources_used = [node for node, status in status_dict.items() if status == "success"]
    
    # Produce the cross-domain structured dictionary
    report = {
        "molecule": molecule,
        "summary": {
            "clinical_signal": c_data.get("summary", {}).get("most_common_condition", "No clinical summary available.") if isinstance(c_data.get("summary"), dict) else c_data.get("summary", "No clinical summary available."),
            "literature_signal": "Success" if l_data.get("status") == "success" else "No literature signal available.",
            "patent_status": p_data.get("patent_status", "No patent status available."),
            "regulatory_status": r_data.get("data", {}).get("regulatory_summary", "No regulatory summary") if isinstance(r_data.get("data"), dict) else "No regulatory data",
            "market_signal": m_data.get("market_potential", "No market signal available.")
        },
        "evidence": {
            "clinical_trials": c_data.get("trials", []),
            "papers": l_data.get("findings", []),
            "patents": p_data.get("detailed_analysis", {}).get("citations", []),
            "approvals": r_data.get("data", {}).get("approved_indications", []) if isinstance(r_data.get("data"), dict) else []
        },
        "meta": {
            "confidence": "medium",  # placeholder, can build heuristic later
            "sources_used": sources_used
        }
    }
    
    return report
