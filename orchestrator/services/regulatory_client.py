import httpx
from typing import Dict, Any
from orchestrator.config import settings
from orchestrator.utils.logger import logger

async def fetch_regulatory_data(molecule: str) -> Dict[str, Any]:
    payload = {"molecule": molecule}
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(settings.REGULATORY_AGENT_URL, json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Regulatory agent failed for '{molecule}': {str(e)}")
        raise
