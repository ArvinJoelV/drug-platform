from orchestrator.graph.state import OrchestratorState
from orchestrator.utils.normalizer import build_final_report
from orchestrator.graph.nodes.failure_handler import safe_node

@safe_node("aggregator")
async def aggregator_node(state: OrchestratorState) -> dict:
    # Use deterministic logic to merge all independent state dicts into a final JSON report
    report = build_final_report(state)
    return {"final_report": report, "status": {"aggregator": "success"}, "errors": {}}
