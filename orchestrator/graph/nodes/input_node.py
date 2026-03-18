from orchestrator.graph.state import OrchestratorState

def input_node(state: OrchestratorState) -> dict:
    # Initialize the basic state properties
    return {
        "molecule": state["molecule"],
        "status": {"input": "initialized"}
    }
