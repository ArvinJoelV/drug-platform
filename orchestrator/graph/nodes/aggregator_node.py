from orchestrator.graph.state import OrchestratorState
from orchestrator.utils.normalizer import build_final_report
from orchestrator.graph.nodes.failure_handler import safe_node

@safe_node("aggregator")
async def aggregator_node(state: OrchestratorState) -> dict:
    report = build_final_report(state, include_derived=False)
    return {"aggregated_report": report, "status": {"aggregator": "success"}, "errors": {}}
