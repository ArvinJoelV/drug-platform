import httpx
from typing import Dict, Any, Optional
from orchestrator.config import settings
from orchestrator.utils.logger import logger

async def fetch_literature_data(molecule: str, clinical_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = {"query": _build_literature_query(molecule, clinical_data)}
    if clinical_data:
        payload["clinical_context"] = clinical_data
        
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(settings.LITERATURE_AGENT_URL, json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Literature agent failed for '{molecule}': {str(e)}")
        raise


def _build_literature_query(molecule: str, clinical_data: Optional[Dict[str, Any]]) -> str:
    if not clinical_data:
        return molecule

    diseases: list[str] = []
    summary = clinical_data.get("summary", {}) if isinstance(clinical_data.get("summary"), dict) else {}

    most_common = summary.get("most_common_condition")
    if most_common:
        diseases.append(str(most_common))

    for condition in summary.get("conditions", []) or []:
        condition_text = str(condition).strip()
        if condition_text and condition_text not in diseases:
            diseases.append(condition_text)

    enriched_tail = " ".join(diseases[:3]).strip()
    return f"{molecule} {enriched_tail}".strip()
