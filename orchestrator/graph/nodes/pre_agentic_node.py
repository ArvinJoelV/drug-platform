from orchestrator.graph.nodes.failure_handler import safe_node
from orchestrator.graph.state import OrchestratorState
from orchestrator.services.mechanism_service import resolve_mechanism_context


@safe_node("pre_agentic")
async def pre_agentic_node(state: OrchestratorState) -> dict:
    molecule = state["molecule"]
    mechanism_context = resolve_mechanism_context(molecule)
    return {
        "mechanism_context": mechanism_context,
        "status": {"pre_agentic": "success"},
        "errors": {},
    }
