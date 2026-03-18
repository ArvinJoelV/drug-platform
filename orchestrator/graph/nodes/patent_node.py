from orchestrator.graph.state import OrchestratorState
from orchestrator.services.patent_client import fetch_patent_data
from orchestrator.graph.nodes.failure_handler import safe_node

@safe_node("patent")
async def patent_node(state: OrchestratorState) -> dict:
    molecule = state["molecule"]
    try:
        data = await fetch_patent_data(molecule)
        return {"patent_data": data, "status": {"patent": "success"}, "errors": {}}
    except Exception as e:
        return {"patent_data": None, "errors": {"patent": str(e)}, "status": {"patent": "timeout_or_failed"}}
