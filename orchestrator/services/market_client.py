import httpx
from typing import Dict, Any
from orchestrator.config import settings
from orchestrator.utils.logger import logger

async def fetch_market_data(molecule: str) -> Dict[str, Any]:
    # Simple approximate mapping as per requirement
    molecule_to_disease = {
        "metformin": "diabetes",
        "aspirin": "pain relief",
        "ibuprofen": "inflammation",
        "paracetamol": "fever",
        "aducanumab": "alzheimer's"
    }
    
    disease = molecule_to_disease.get(molecule.lower(), molecule)
    payload = {"disease": disease}
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(settings.MARKET_AGENT_URL, json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Market agent failed for '{molecule}': {str(e)}")
        raise
