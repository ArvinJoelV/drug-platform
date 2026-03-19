from orchestrator.graph.nodes.failure_handler import safe_node
from orchestrator.graph.state import OrchestratorState
from orchestrator.utils.normalizer import build_final_report


@safe_node("finalizer")
async def finalizer_node(state: OrchestratorState) -> dict:
    report = build_final_report(state)
    return {"final_report": report, "status": {"finalizer": "success"}, "errors": {}}
