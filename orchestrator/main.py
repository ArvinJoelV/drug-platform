from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from orchestrator.graph.orchestrator_graph import graph
from orchestrator.services.analysis_store import analysis_store

app = FastAPI(title="Drug Platform Orchestrator")

class OrchestratorRequest(BaseModel):
    molecule: str

async def _run_analysis(request: OrchestratorRequest):
    analysis_id = analysis_store.create_pending(request.molecule)
    initial_state = {"molecule": request.molecule, "analysis_id": analysis_id}

    try:
        final_state = await graph.ainvoke(initial_state)
        report = final_state.get("final_report", {})
        report["analysis_id"] = analysis_id

        if final_state.get("errors"):
            report["agent_errors"] = final_state["errors"]

        analysis_store.complete(analysis_id, report)
        return report
    except Exception as e:
        analysis_store.fail(analysis_id, str(e))
        raise HTTPException(status_code=500, detail=f"Orchestration Global Failure: {str(e)}")


@app.post("/analyze")
async def analyze(request: OrchestratorRequest):
    return await _run_analysis(request)


@app.post("/orchestrate")
async def orchestrate(request: OrchestratorRequest):
    return await _run_analysis(request)


def _get_record_or_404(analysis_id: str) -> dict:
    record = analysis_store.get(analysis_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Analysis not found: {analysis_id}")
    return record


@app.get("/analysis/{analysis_id}/status")
async def get_analysis_status(analysis_id: str):
    status = analysis_store.status(analysis_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Analysis not found: {analysis_id}")
    return status


@app.get("/analysis/{analysis_id}/partial")
async def get_analysis_partial(analysis_id: str):
    record = _get_record_or_404(analysis_id)
    return {
        "analysis_id": analysis_id,
        "status": record["status"],
        "result": record.get("result"),
        "error": record.get("error"),
    }


@app.get("/analysis/{analysis_id}/summary")
async def get_analysis_summary(analysis_id: str):
    record = _get_record_or_404(analysis_id)
    result = record.get("result") or {}
    return {
        "analysis_id": analysis_id,
        "molecule": result.get("molecule", record.get("molecule")),
        "mechanism_context": result.get("mechanism_context", {}),
        "summary": result.get("summary", {}),
        "meta": result.get("meta", {}),
    }


@app.get("/analysis/{analysis_id}/evidence")
async def get_analysis_evidence(analysis_id: str):
    record = _get_record_or_404(analysis_id)
    result = record.get("result") or {}
    return {
        "analysis_id": analysis_id,
        "molecule": result.get("molecule", record.get("molecule")),
        "evidence": result.get("evidence", {}),
    }


@app.get("/analysis/{analysis_id}/intelligence")
async def get_analysis_intelligence(analysis_id: str):
    record = _get_record_or_404(analysis_id)
    result = record.get("result") or {}
    return {
        "analysis_id": analysis_id,
        "molecule": result.get("molecule", record.get("molecule")),
        "intelligence": result.get("intelligence", {}),
        "contradictions": result.get("contradictions", {}),
        "mechanism_context": result.get("mechanism_context", {}),
    }


@app.get("/analysis/{analysis_id}/contradictions")
async def get_analysis_contradictions(analysis_id: str):
    record = _get_record_or_404(analysis_id)
    result = record.get("result") or {}
    return {
        "analysis_id": analysis_id,
        "molecule": result.get("molecule", record.get("molecule")),
        "mechanism_context": result.get("mechanism_context", {}),
        "contradictions": result.get("contradictions", {}),
    }


@app.get("/analysis/{analysis_id}/report")
async def get_analysis_report(analysis_id: str):
    record = _get_record_or_404(analysis_id)
    result = record.get("result") or {}
    return {
        "analysis_id": analysis_id,
        "molecule": result.get("molecule", record.get("molecule")),
        "llm_report": result.get("llm_report", {}),
    }


@app.get("/analysis/{analysis_id}/agents")
async def get_analysis_agents(analysis_id: str):
    record = _get_record_or_404(analysis_id)
    result = record.get("result") or {}
    return {
        "analysis_id": analysis_id,
        "molecule": result.get("molecule", record.get("molecule")),
        "agents": result.get("agents", {}),
        "agent_errors": result.get("agent_errors", {}),
    }

# This ensures users can just do `uvicorn orchestrator.main:app --port 8000`
