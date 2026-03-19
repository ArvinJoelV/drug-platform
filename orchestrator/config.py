import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    # Agent endpoints (running independently)
    CLINICAL_AGENT_URL: str = os.getenv("CLINICAL_AGENT_URL", "http://localhost:8001/analyze")
    LITERATURE_AGENT_URL: str = os.getenv("LITERATURE_AGENT_URL", "http://localhost:8002/analyze")
    PATENT_AGENT_URL: str = os.getenv("PATENT_AGENT_URL", "http://localhost:8003/analyze")
    MARKET_AGENT_URL: str = os.getenv("MARKET_AGENT_URL", "http://localhost:8004/analyze")
    REGULATORY_AGENT_URL: str = os.getenv("REGULATORY_AGENT_URL", "http://localhost:8005/regulatory")
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
    GEMINI_TEMPERATURE: float = float(os.getenv("GEMINI_TEMPERATURE", "0.1"))
    GEMINI_MAX_TOKENS: int = int(os.getenv("GEMINI_MAX_TOKENS", "2048"))

settings = Settings()
