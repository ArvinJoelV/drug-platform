from orchestrator.graph.state import OrchestratorState
from orchestrator.services.literature_client import fetch_literature_data
from orchestrator.graph.nodes.failure_handler import safe_node

@safe_node("literature")
async def literature_node(state: OrchestratorState) -> dict:
    molecule = state["molecule"]
    clinical_data = state.get("clinical_data")
    mechanism_context = state.get("mechanism_context")
    try:
        # Passes clinical_data if available (dependency flow)
        data = await fetch_literature_data(
            molecule,
            clinical_data=clinical_data,
            mechanism_context=mechanism_context,
        )
        return {"literature_data": data, "status": {"literature": "success"}, "errors": {}}
    except Exception as e:
        return {"literature_data": None, "errors": {"literature": str(e)}, "status": {"literature": "timeout_or_failed"}}
