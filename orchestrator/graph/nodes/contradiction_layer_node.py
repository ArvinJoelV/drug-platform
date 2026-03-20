from orchestrator.graph.nodes.failure_handler import safe_node
from orchestrator.graph.state import OrchestratorState
from orchestrator.utils.contradictions import build_contradiction_payload, apply_contradiction_adjustments


@safe_node("contradiction_layer")
async def contradiction_layer_node(state: OrchestratorState) -> dict:
    intelligence = state.get("intelligence_data") or {}
    contradictions = build_contradiction_payload(state, intelligence)
    adjusted_intelligence = apply_contradiction_adjustments(intelligence, contradictions)
    return {
        "contradictions": contradictions,
        "reviewed_intelligence_data": adjusted_intelligence,
        "status": {"contradiction_layer": "success"},
        "errors": {},
    }
