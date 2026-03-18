from orchestrator.graph.state import OrchestratorState
from orchestrator.services.regulatory_client import fetch_regulatory_data
from orchestrator.graph.nodes.failure_handler import safe_node

@safe_node("regulatory")
async def regulatory_node(state: OrchestratorState) -> dict:
    molecule = state["molecule"]
    try:
        data = await fetch_regulatory_data(molecule)
        return {"regulatory_data": data, "status": {"regulatory": "success"}, "errors": {}}
    except Exception as e:
        return {"regulatory_data": None, "errors": {"regulatory": str(e)}, "status": {"regulatory": "timeout_or_failed"}}
