from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from orchestrator.graph.orchestrator_graph import graph

app = FastAPI(title="Drug Platform Orchestrator")

class OrchestratorRequest(BaseModel):
    molecule: str

@app.post("/orchestrate")
async def orchestrate(request: OrchestratorRequest):
    initial_state = {"molecule": request.molecule}
    
    try:
        # Asynchronously invoke graph using StateGraph inputs
        final_state = await graph.ainvoke(initial_state)
        
        # Build deterministic API response
        report = final_state.get("final_report", {})
        
        # Attach any network or sub-agent errors to expose transparently
        if final_state.get("errors"):
            report["agent_errors"] = final_state["errors"]
            
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Orchestration Global Failure: {str(e)}")

# This ensures users can just do `uvicorn orchestrator.main:app --port 8000`
