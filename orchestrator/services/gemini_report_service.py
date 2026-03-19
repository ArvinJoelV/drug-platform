from __future__ import annotations

import json
from typing import Any, Dict, Optional

from orchestrator.config import settings
from orchestrator.utils.logger import logger

try:
    from google import genai
    from google.genai import types
except Exception:  # pragma: no cover - optional dependency
    genai = None
    types = None


class GeminiReportService:
    def __init__(self) -> None:
        self._client = None
        self._available = False

        if not genai:
            logger.warning("google-genai is not installed; using deterministic report fallback")
            return

        try:
            if settings.GEMINI_API_KEY:
                self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
            else:
                self._client = genai.Client()
            self._available = True
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.warning(f"Gemini client initialization failed, using fallback: {exc}")

    @property
    def available(self) -> bool:
        return self._available and self._client is not None and types is not None

    def generate_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.available:
            return self._fallback_report(payload, reason="Gemini unavailable")

        prompt = self._build_prompt(payload)
        try:
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)],
                )
            ]
            config = types.GenerateContentConfig(
                temperature=settings.GEMINI_TEMPERATURE,
                max_output_tokens=settings.GEMINI_MAX_TOKENS,
                response_mime_type="application/json",
            )

            response_text = ""
            for chunk in self._client.models.generate_content_stream(
                model=settings.GEMINI_MODEL,
                contents=contents,
                config=config,
            ):
                if chunk.text:
                    response_text += chunk.text

            parsed = json.loads(response_text)
            if not isinstance(parsed, dict):
                raise ValueError("Gemini report response was not a JSON object")

            return {
                "executive_summary": parsed.get("executive_summary", ""),
                "key_findings": parsed.get("key_findings", []),
                "top_repurposing_opportunities": parsed.get("top_repurposing_opportunities", []),
                "risks_and_limitations": parsed.get("risks_and_limitations", []),
                "final_recommendation": parsed.get("final_recommendation", ""),
                "generation_mode": "gemini",
                "model": settings.GEMINI_MODEL,
            }
        except Exception as exc:  # pragma: no cover - network dependent
            logger.warning(f"Gemini report generation failed, using fallback: {exc}")
            return self._fallback_report(payload, reason=str(exc))

    def _build_prompt(self, payload: Dict[str, Any]) -> str:
        return (
            "You are preparing a concise drug repurposing decision memo.\n"
            "Use ONLY the structured JSON payload below.\n"
            "Do not invent evidence, scores, approvals, or claims.\n"
            "Return strict JSON with keys: executive_summary, key_findings, "
            "top_repurposing_opportunities, risks_and_limitations, final_recommendation.\n"
            "key_findings, top_repurposing_opportunities, and risks_and_limitations must be arrays of strings.\n\n"
            f"PAYLOAD:\n{json.dumps(payload, indent=2)}"
        )

    def _fallback_report(self, payload: Dict[str, Any], reason: Optional[str] = None) -> Dict[str, Any]:
        opportunities = payload.get("intelligence", {}).get("top_opportunities", []) or []
        insights = payload.get("intelligence", {}).get("cross_domain_insights", []) or []
        summary = payload.get("summary", {}) or {}

        top_lines = []
        for item in opportunities[:3]:
            disease = item.get("disease", "Unknown")
            score = item.get("score", 0)
            confidence = item.get("confidence", "low")
            top_lines.append(f"{disease} scored {score} with {confidence} confidence.")

        risk_lines = []
        for insight in insights[:3]:
            for flag in insight.get("risk_flags", [])[:2]:
                risk_lines.append(flag)

        recommendation = (
            f"Prioritize {opportunities[0].get('disease')} for follow-up validation."
            if opportunities
            else "No strong repurposing opportunity was identified from the current evidence."
        )

        return {
            "executive_summary": (
                f"{payload.get('molecule', 'This molecule')} was analyzed across clinical, literature, "
                f"patent, regulatory, and market signals. Clinical signal: "
                f"{summary.get('clinical_signal', 'unknown')}; market signal: "
                f"{summary.get('market_signal', 'unknown')}."
            ),
            "key_findings": top_lines or ["Evidence was assembled, but no ranked opportunity cleared the scoring threshold."],
            "top_repurposing_opportunities": [item.get("rationale", "") for item in opportunities[:3] if item.get("rationale")],
            "risks_and_limitations": risk_lines or ["Cross-domain evidence is incomplete for some candidate diseases."],
            "final_recommendation": recommendation,
            "generation_mode": "fallback",
            "model": settings.GEMINI_MODEL,
            "fallback_reason": reason or "Gemini unavailable",
        }


gemini_report_service = GeminiReportService()
