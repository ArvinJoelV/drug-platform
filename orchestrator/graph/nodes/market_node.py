from orchestrator.graph.state import OrchestratorState
from orchestrator.services.market_client import fetch_market_data
from orchestrator.graph.nodes.failure_handler import safe_node

@safe_node("market")
async def market_node(state: OrchestratorState) -> dict:
    molecule = state["molecule"]
    try:
        data = await fetch_market_data(molecule)
        return {"market_data": data, "status": {"market": "success"}, "errors": {}}
    except Exception as e:
        return {"market_data": None, "errors": {"market": str(e)}, "status": {"market": "timeout_or_failed"}}
