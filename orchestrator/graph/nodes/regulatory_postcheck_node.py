from orchestrator.graph.nodes.failure_handler import safe_node
from orchestrator.graph.state import OrchestratorState
from orchestrator.utils.intelligence import build_posthoc_regulatory_check


@safe_node("regulatory_postcheck")
async def regulatory_postcheck_node(state: OrchestratorState) -> dict:
    intelligence = state.get("reviewed_intelligence_data") or state.get("intelligence_data") or {}
    postcheck = build_posthoc_regulatory_check(intelligence, state)
    return {
        "regulatory_postcheck": postcheck,
        "status": {"regulatory_postcheck": "success"},
        "errors": {},
    }
