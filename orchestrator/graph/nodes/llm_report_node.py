from orchestrator.graph.nodes.failure_handler import safe_node
from orchestrator.graph.state import OrchestratorState
from orchestrator.services.gemini_report_service import gemini_report_service


@safe_node("llm_report")
async def llm_report_node(state: OrchestratorState) -> dict:
    aggregated = state.get("aggregated_report") or {}
    intelligence = state.get("intelligence_data") or {}
    postcheck = state.get("regulatory_postcheck") or {}

    payload = {
        "molecule": state.get("molecule"),
        "summary": aggregated.get("summary", {}),
        "key_evidence": aggregated.get("evidence", {}),
        "intelligence": {
            "top_opportunities": intelligence.get("top_opportunities", []),
            "cross_domain_insights": intelligence.get("cross_domain_insights", []),
            "confidence_breakdown": intelligence.get("confidence_breakdown", {}),
            "regulatory_postcheck": postcheck,
        },
    }
    report = gemini_report_service.generate_report(payload)
    return {"llm_report": report, "status": {"llm_report": "success"}, "errors": {}}
