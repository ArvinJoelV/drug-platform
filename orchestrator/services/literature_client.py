import httpx
from typing import Dict, Any, Optional
from orchestrator.config import settings
from orchestrator.utils.logger import logger

async def fetch_literature_data(molecule: str, clinical_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = {"query": molecule}
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
