from orchestrator.graph.state import OrchestratorState

def input_node(state: OrchestratorState) -> dict:
    # Initialize the basic state properties
    return {
        "molecule": state["molecule"],
        "mechanism_context": state.get("mechanism_context"),
        "status": {"input": "initialized"}
    }
