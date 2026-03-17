from google import genai
from google.genai import types
import logging
from typing import Optional, Dict, Any, List
from models import RegulatoryIntelligence, RetrievedChunk
from config import GEMINI_MODEL, GEMINI_TEMPERATURE, GEMINI_MAX_TOKENS

logger = logging.getLogger(__name__)


class GeminiReasoningLayer:
    """
    Gemini LLM integration for structured regulatory intelligence synthesis.
    Converts raw context into organized, actionable insights.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = None):
        """
        Initialize Gemini client.
        """
        self.model_name = model or GEMINI_MODEL
        self.temperature = GEMINI_TEMPERATURE
        self.max_tokens = GEMINI_MAX_TOKENS
        
        # Configure Gemini with new SDK
        if api_key:
            self.client = genai.Client(api_key=api_key)
            logger.info("Gemini client initialized with provided API key")
        else:
            self.client = genai.Client()  # Will use GEMINI_API_KEY from environment
            logger.info("Gemini client initialized with environment API key")
        
        logger.info(f"GeminiReasoningLayer initialized with model: {self.model_name}")
    
    def synthesize(self, drug_name: str, context: str, 
               chunks: Optional[List[RetrievedChunk]] = None) -> RegulatoryIntelligence:
        """
        Main method - synthesize regulatory intelligence from context.
        """
        # Build the prompt
        prompt = self._build_prompt(drug_name, context)
        
        try:
            # Log that we're attempting API call
            logger.info(f"Calling Gemini API for {drug_name}")
            
            # Create content
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                    ],
                ),
            ]
            
            # Configure generation
            generate_content_config = types.GenerateContentConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )
            
            # Call Gemini with streaming and collect full response
            response_text = ""
            for chunk in self.client.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
                config=generate_content_config,
            ):
                if chunk.text:
                    response_text += chunk.text
                    # Optional: print for debugging
                    # print(chunk.text, end="")
            
            logger.info(f"Gemini API call successful for {drug_name}")
            logger.debug(f"Full response length: {len(response_text)} characters")
            
            # Parse response
            intelligence = self._parse_response(response_text, drug_name)
            
            # Add sources from chunks if provided
            if chunks:
                sources = set()
                for chunk in chunks:
                    if chunk.source:
                        sources.add(chunk.source)
                intelligence.sources = list(sources)
            
            logger.info(f"Successfully synthesized intelligence for {drug_name}")
            logger.info(f"Found {len(intelligence.approved_indications)} indications, "
                    f"{len(intelligence.warnings)} warnings, "
                    f"{len(intelligence.contradictions)} contraindications, "
                    f"{len(intelligence.adverse_events)} adverse events")
            
            return intelligence
            
        except Exception as e:
            logger.error(f"Gemini synthesis failed: {e}")
            # Return empty intelligence on failure
            return RegulatoryIntelligence(
                drug=drug_name,
                regulatory_summary=f"Failed to synthesize regulatory data: {str(e)}",
                confidence=0.0
            )
    
    def _build_prompt(self, drug_name: str, context: str) -> str:
        """
        Build the prompt for Gemini with strict grounding constraints.
        """
        prompt = f"""You are a regulatory intelligence analyst. Your task is to extract structured information about {drug_name} from the provided regulatory context.

IMPORTANT RULES:
1. ONLY use information from the provided context below
2. Do NOT add any external knowledge or hallucinations
3. If information is not found in the context, leave that field empty
4. Be precise and concise
5. Format responses as bullet points

CONTEXT:
{context}

Based STRICTLY on the above context, provide the following information about {drug_name}:

1. APPROVED INDICATIONS:
   List all approved medical uses, diseases, or conditions.
   (Bullet points, each starting with "•")

2. WARNINGS:
   List all safety warnings, precautions, and risk information.
   (Bullet points, each starting with "•")

3. CONTRAINDICATIONS:
   List all situations where the drug should NOT be used.
   (Bullet points, each starting with "•")

4. ADVERSE EVENTS:
   List all side effects and adverse reactions.
   (Bullet points, each starting with "•")

5. REGULATORY SUMMARY:
   Write a brief 2-3 sentence summary of the drug's regulatory profile.
   Include overall safety profile and key usage patterns.

Remember: Only use information from the context provided above."""
        
        return prompt
    
    def _parse_response(self, response_text: str, drug_name: str) -> RegulatoryIntelligence:
        """
        Parse Gemini's response into structured format.
        """
        intelligence = RegulatoryIntelligence(drug=drug_name)
        
        if not response_text:
            logger.warning(f"Empty response for {drug_name}")
            return intelligence
        
        # Parse sections
        current_section = None
        lines = response_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for section headers (more flexible matching)
            lower_line = line.lower()
            if "approved indications" in lower_line or "1." in line and "indications" in lower_line:
                current_section = "indications"
            elif "warnings" in lower_line and "2." in line or "warnings" in lower_line and not "contraindications" in lower_line:
                current_section = "warnings"
            elif "contraindications" in lower_line or "3." in line and "contraindications" in lower_line:
                current_section = "contradictions"
            elif "adverse events" in lower_line or "4." in line and "adverse" in lower_line:
                current_section = "adverse"
            elif "regulatory summary" in lower_line or "5." in line and "summary" in lower_line:
                current_section = "summary"
            
            # Parse bullet points (handle various bullet formats)
            elif line.startswith('•') or line.startswith('-') or line.startswith('*') or line.startswith('**'):
                # Clean up the bullet point
                content = line.lstrip('•-* ').strip()
                if content and len(content) > 3:  # Only add meaningful content
                    if current_section == "indications":
                        intelligence.approved_indications.append(content)
                    elif current_section == "warnings":
                        intelligence.warnings.append(content)
                    elif current_section == "contradictions":
                        intelligence.contradictions.append(content)
                    elif current_section == "adverse":
                        intelligence.adverse_events.append(content)
            
            # Summary (multi-line) - collect all text after summary header
            elif current_section == "summary" and line:
                if intelligence.regulatory_summary:
                    intelligence.regulatory_summary += " " + line
                else:
                    intelligence.regulatory_summary = line
        
        # Clean up any incomplete sentences in indications
        intelligence.approved_indications = [ind for ind in intelligence.approved_indications if ind and len(ind) > 5]
        intelligence.warnings = [w for w in intelligence.warnings if w and len(w) > 5]
        intelligence.contradictions = [c for c in intelligence.contradictions if c and len(c) > 5]
        intelligence.adverse_events = [a for a in intelligence.adverse_events if a and len(a) > 5]
        
        return intelligence
    
    @staticmethod
    def fallback_extraction(drug_name: str, chunks: List[RetrievedChunk]) -> RegulatoryIntelligence:
        """
        Fallback method when Gemini is unavailable.
        Uses simple heuristics to extract information.
        """
        from context_builder import ContextBuilder
        
        builder = ContextBuilder()
        key_facts = builder.extract_key_facts(chunks)
        
        intelligence = RegulatoryIntelligence(
            drug=drug_name,
            approved_indications=key_facts.get("indications", []),
            warnings=key_facts.get("warnings", []),
            contradictions=key_facts.get("contradictions", []),
            adverse_events=key_facts.get("adverse", []),
            regulatory_summary="Extracted via fallback method (LLM unavailable)",
            confidence=0.3  # Low confidence for fallback
        )
        
        # Add sources
        sources = set(ch.source for ch in chunks if ch.source)
        intelligence.sources = list(sources)
        
        logger.warning(f"Used fallback extraction for {drug_name}")
        return intelligence