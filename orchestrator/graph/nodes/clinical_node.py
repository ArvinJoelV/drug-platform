from orchestrator.graph.state import OrchestratorState
from orchestrator.services.clinical_client import fetch_clinical_data
from orchestrator.graph.nodes.failure_handler import safe_node

@safe_node("clinical")
async def clinical_node(state: OrchestratorState) -> dict:
    molecule = state["molecule"]
    try:
        data = await fetch_clinical_data(molecule)
        return {"clinical_data": data, "status": {"clinical": "success"}, "errors": {}}
    except Exception as e:
        return {"clinical_data": None, "errors": {"clinical": str(e)}, "status": {"clinical": "timeout_or_failed"}}
