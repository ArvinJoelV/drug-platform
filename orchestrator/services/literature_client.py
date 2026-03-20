import httpx
from typing import Dict, Any, Optional
from orchestrator.config import settings
from orchestrator.utils.logger import logger

async def fetch_literature_data(
    molecule: str,
    clinical_data: Optional[Dict[str, Any]] = None,
    mechanism_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload = {"query": _build_literature_query(molecule, clinical_data, mechanism_context)}
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


def _build_literature_query(
    molecule: str,
    clinical_data: Optional[Dict[str, Any]],
    mechanism_context: Optional[Dict[str, Any]],
) -> str:
    parts: list[str] = [molecule]
    diseases: list[str] = []
    if clinical_data:
        summary = clinical_data.get("summary", {}) if isinstance(clinical_data.get("summary"), dict) else {}

        most_common = summary.get("most_common_condition")
        if most_common:
            diseases.append(str(most_common))

        for condition in summary.get("conditions", []) or []:
            condition_text = str(condition).strip()
            if condition_text and condition_text not in diseases:
                diseases.append(condition_text)

    if diseases:
        parts.append(" ".join(diseases[:3]).strip())

    mechanism_terms = _extract_mechanism_terms(mechanism_context)
    if mechanism_terms:
        parts.append(" ".join(mechanism_terms))

    return " ".join(part for part in parts if part).strip()


def _extract_mechanism_terms(mechanism_context: Optional[Dict[str, Any]]) -> list[str]:
    if not mechanism_context:
        return []

    terms: list[str] = []
    primary_target = str(mechanism_context.get("primary_target") or "").strip()
    primary_action = str(mechanism_context.get("primary_action") or "").strip()
    if primary_target:
        terms.append(primary_target)
    if primary_action:
        terms.append(primary_action)

    for target in mechanism_context.get("targets", []) or []:
        name = str(target.get("name") or "").strip()
        if name and name not in terms:
            terms.append(name)

    for pathway in mechanism_context.get("pathways", []) or []:
        text = str(pathway).strip()
        if text and text not in terms:
            terms.append(text)

    return terms[:6]
