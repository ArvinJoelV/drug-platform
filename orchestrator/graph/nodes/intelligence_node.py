from orchestrator.graph.nodes.failure_handler import safe_node
from orchestrator.graph.state import OrchestratorState
from orchestrator.utils.intelligence import build_intelligence_payload


@safe_node("intelligence")
async def intelligence_node(state: OrchestratorState) -> dict:
    aggregated_report = state.get("aggregated_report") or {}
    intelligence = build_intelligence_payload(aggregated_report, state)
    return {
        "intelligence_data": intelligence,
        "status": {"intelligence": "success"},
        "errors": {},
    }
