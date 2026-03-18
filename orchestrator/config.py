import os
from pydantic import BaseModel

class Settings(BaseModel):
    # Agent endpoints (running independently)
    CLINICAL_AGENT_URL: str = os.getenv("CLINICAL_AGENT_URL", "http://localhost:8001/analyze")
    LITERATURE_AGENT_URL: str = os.getenv("LITERATURE_AGENT_URL", "http://localhost:8002/analyze")
    PATENT_AGENT_URL: str = os.getenv("PATENT_AGENT_URL", "http://localhost:8003/analyze")
    MARKET_AGENT_URL: str = os.getenv("MARKET_AGENT_URL", "http://localhost:8004/analyze")
    REGULATORY_AGENT_URL: str = os.getenv("REGULATORY_AGENT_URL", "http://localhost:8005/regulatory")

settings = Settings()
