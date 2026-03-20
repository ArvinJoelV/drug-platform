from typing import Dict, Any, Optional
from orchestrator.graph.state import OrchestratorState

def _agent_payload(
    state: OrchestratorState,
    agent_name: str,
    state_key: str,
) -> Dict[str, Any]:
    status_dict = state.get("status", {}) or {}
    errors = state.get("errors", {}) or {}
    response: Optional[Dict[str, Any]] = state.get(state_key)

    return {
        "status": status_dict.get(agent_name, "not_run"),
        "error": errors.get(agent_name),
        "response": response,
    }


def build_final_report(state: OrchestratorState, include_derived: bool = True) -> Dict[str, Any]:
    molecule = state.get("molecule", "Unknown")
    analysis_id = state.get("analysis_id")
    mechanism_context = state.get("mechanism_context") or {}
    contradictions = state.get("contradictions") or {}
    
    # Extract data safely with fallbacks
    c_data = state.get("clinical_data") or {}
    l_data = state.get("literature_data") or {}
    p_data = state.get("patent_data") or {}
    r_data = state.get("regulatory_data") or {}
    m_data = state.get("market_data") or {}
    
    # Calculate successful source list
    status_dict = state.get("status", {})
    source_nodes = {"clinical", "literature", "patent", "regulatory", "market"}
    sources_used = [
        node for node, status in status_dict.items()
        if node in source_nodes and status == "success"
    ]

    agent_responses = {
        "clinical": _agent_payload(state, "clinical", "clinical_data"),
        "literature": _agent_payload(state, "literature", "literature_data"),
        "patent": _agent_payload(state, "patent", "patent_data"),
        "regulatory": _agent_payload(state, "regulatory", "regulatory_data"),
        "market": _agent_payload(state, "market", "market_data"),
    }

    # Produce the cross-domain structured dictionary
    report = {
        "analysis_id": analysis_id,
        "molecule": molecule,
        "mechanism_context": mechanism_context,
        "summary": {
            "clinical_signal": c_data.get("summary", {}).get("most_common_condition", "No clinical summary available.") if isinstance(c_data.get("summary"), dict) else c_data.get("summary", "No clinical summary available."),
            "literature_signal": "Success" if l_data.get("status") == "success" else "No literature signal available.",
            "patent_status": p_data.get("patent_status", "No patent status available."),
            "regulatory_status": r_data.get("data", {}).get("regulatory_summary", "No regulatory summary") if isinstance(r_data.get("data"), dict) else "No regulatory data",
            "market_signal": m_data.get("market_potential", "No market signal available."),
            "mechanism_signal": mechanism_context.get("primary_target") or "No mechanism context available.",
        },
        "evidence": {
            "clinical_trials": c_data.get("trials", []),
            "papers": l_data.get("findings", []),
            "patents": p_data.get("detailed_analysis", {}).get("citations", []),
            "approvals": r_data.get("data", {}).get("approved_indications", []) if isinstance(r_data.get("data"), dict) else [],
            "regulatory": r_data.get("data", {}) if isinstance(r_data.get("data"), dict) else {},
            "market": {
                "disease": m_data.get("disease"),
                "market_potential": m_data.get("market_potential"),
                "global_prevalence": m_data.get("global_prevalence"),
                "market_growth": m_data.get("market_growth"),
                "key_statistics": m_data.get("detailed_analysis", {}).get("key_statistics", []),
            },
            "mechanism": mechanism_context,
        },
        "meta": {
            "confidence": "medium",  # placeholder, can build heuristic later
            "sources_used": sources_used
        },
        "agents": agent_responses,
    }

    if include_derived:
        intelligence = state.get("reviewed_intelligence_data") or state.get("intelligence_data") or {}
        report["intelligence"] = intelligence
        report["contradictions"] = contradictions
        report["llm_report"] = state.get("llm_report") or {}
        report["meta"]["confidence"] = intelligence.get("confidence_breakdown", {}).get("global_confidence", "medium")
        report["meta"]["contradiction_risk"] = contradictions.get("summary", {}).get("risk_level", "low")
        if state.get("regulatory_postcheck"):
            report["meta"]["regulatory_postcheck"] = state["regulatory_postcheck"]
    
    return report
