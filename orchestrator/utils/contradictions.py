from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List


def build_contradiction_payload(state: Dict[str, Any], intelligence: Dict[str, Any]) -> Dict[str, Any]:
    normalized = intelligence.get("normalized_signals", {}) or {}
    insights = intelligence.get("cross_domain_insights", []) or []
    regulatory_data = state.get("regulatory_data") or {}
    regulatory_core = regulatory_data.get("data", {}) if isinstance(regulatory_data.get("data"), dict) else {}
    mechanism = state.get("mechanism_context") or {}

    clinical_map = _ranked_list_to_map(normalized.get("clinical", {}).get("diseases", []))
    literature_map = _ranked_list_to_map(normalized.get("literature", {}).get("diseases", []))
    approved_text = " ".join(regulatory_core.get("approved_indications", []) or []).lower()
    market_disease = str(normalized.get("market", {}).get("disease") or "").lower()

    contradictions: List[Dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for insight in insights:
        disease = str(insight.get("disease") or "").strip()
        if not disease:
            continue

        clinical_hits = clinical_map.get(disease, 0)
        literature_hits = literature_map.get(disease, 0)

        if literature_hits and not clinical_hits:
            _append_contradiction(
                contradictions,
                seen,
                disease=disease,
                type_="clinical_vs_literature",
                severity="high",
                message="Literature is positive, but no matching clinical validation signal was found.",
                affected_domains=["literature", "clinical"],
            )

        if clinical_hits and not literature_hits:
            _append_contradiction(
                contradictions,
                seen,
                disease=disease,
                type_="clinical_vs_literature",
                severity="medium",
                message="Clinical activity exists, but literature support is sparse or missing.",
                affected_domains=["clinical", "literature"],
            )

        if mechanism.get("resolved") and mechanism.get("primary_target") and not (clinical_hits or literature_hits):
            _append_contradiction(
                contradictions,
                seen,
                disease=disease,
                type_="mechanism_vs_outcome",
                severity="medium",
                message=(
                    f"Mechanism context suggests relevance via {mechanism.get('primary_target')}, "
                    "but no disease-specific translational evidence was detected."
                ),
                affected_domains=["mechanism", "clinical", "literature"],
            )

        if disease.lower() in approved_text:
            _append_contradiction(
                contradictions,
                seen,
                disease=disease,
                type_="regulatory_vs_opportunity",
                severity="high",
                message="This disease already appears in approved indication text, reducing repurposing novelty.",
                affected_domains=["regulatory", "intelligence"],
            )

        if market_disease and (disease.lower() in market_disease or market_disease in disease.lower()) and not clinical_hits:
            _append_contradiction(
                contradictions,
                seen,
                disease=disease,
                type_="market_vs_clinical",
                severity="medium",
                message="Market attractiveness is present, but clinical support is currently weak.",
                affected_domains=["market", "clinical"],
            )

    warnings = regulatory_core.get("warnings", []) or []
    contradictions_from_reg = regulatory_core.get("contradictions", []) or []
    for item in warnings[:3]:
        _append_contradiction(
            contradictions,
            seen,
            disease="general",
            type_="regulatory_warning",
            severity="medium",
            message=str(item),
            affected_domains=["regulatory"],
        )
    for item in contradictions_from_reg[:3]:
        _append_contradiction(
            contradictions,
            seen,
            disease="general",
            type_="regulatory_vs_opportunity",
            severity="high",
            message=str(item),
            affected_domains=["regulatory"],
        )

    severity_counts = {"high": 0, "medium": 0, "low": 0}
    for item in contradictions:
        severity_counts[item["severity"]] = severity_counts.get(item["severity"], 0) + 1

    return {
        "items": contradictions,
        "summary": {
            "total": len(contradictions),
            "severity_counts": severity_counts,
            "risk_level": _risk_level_from_counts(severity_counts),
        },
    }


def apply_contradiction_adjustments(intelligence: Dict[str, Any], contradictions: Dict[str, Any]) -> Dict[str, Any]:
    adjusted = deepcopy(intelligence)
    items = contradictions.get("items", []) or []
    items_by_disease: dict[str, list[Dict[str, Any]]] = {}
    for item in items:
        disease = str(item.get("disease") or "").strip().lower()
        if disease:
            items_by_disease.setdefault(disease, []).append(item)

    for score_item in adjusted.get("confidence_breakdown", {}).get("per_disease_scores", []) or []:
        disease_key = str(score_item.get("disease") or "").strip().lower()
        disease_contradictions = items_by_disease.get(disease_key, [])
        penalty = _penalty_for_contradictions(disease_contradictions)
        original_score = float(score_item.get("score", 0))
        adjusted_score = max(0, round(original_score - penalty, 2))
        score_item["score"] = adjusted_score
        score_item["confidence"] = _score_to_confidence(adjusted_score)
        score_item["drivers"]["contradiction_penalty"] = penalty

    per_disease = adjusted.get("confidence_breakdown", {}).get("per_disease_scores", []) or []
    if per_disease:
        global_score = round(sum(float(item.get("score", 0)) for item in per_disease) / len(per_disease), 2)
        adjusted["confidence_breakdown"]["global_score"] = global_score
        adjusted["confidence_breakdown"]["global_confidence"] = _score_to_confidence(global_score)
    adjusted.setdefault("confidence_breakdown", {}).setdefault("scoring_policy", {})
    adjusted["confidence_breakdown"]["scoring_policy"]["contradiction_mode"] = "penalty"
    adjusted["confidence_breakdown"]["contradictions_summary"] = contradictions.get("summary", {})

    for opportunity in adjusted.get("top_opportunities", []) or []:
        disease_key = str(opportunity.get("disease") or "").strip().lower()
        disease_contradictions = items_by_disease.get(disease_key, [])
        penalty = _penalty_for_contradictions(disease_contradictions)
        original_score = float(opportunity.get("score", 0))
        adjusted_score = max(0, round(original_score - penalty, 2))
        opportunity["score"] = adjusted_score
        opportunity["confidence"] = _score_to_confidence(adjusted_score)
        opportunity["contradiction_count"] = len(disease_contradictions)
        opportunity["risk_flags"] = [item.get("message", "") for item in disease_contradictions[:3] if item.get("message")]

    adjusted["top_opportunities"] = sorted(
        adjusted.get("top_opportunities", []) or [],
        key=lambda item: float(item.get("score", 0)),
        reverse=True,
    )
    adjusted["contradictions"] = contradictions
    return adjusted


def _append_contradiction(
    contradictions: List[Dict[str, Any]],
    seen: set[tuple[str, str]],
    disease: str,
    type_: str,
    severity: str,
    message: str,
    affected_domains: Iterable[str],
) -> None:
    key = (disease.lower(), type_)
    if key in seen:
        return
    seen.add(key)
    contradictions.append(
        {
            "disease": disease,
            "type": type_,
            "severity": severity,
            "message": message,
            "affected_domains": list(affected_domains),
        }
    )


def _ranked_list_to_map(items: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    return {str(item.get("name")): int(item.get("count", 0)) for item in items if item.get("name")}


def _penalty_for_contradictions(items: Iterable[Dict[str, Any]]) -> int:
    penalty = 0
    for item in items:
        severity = str(item.get("severity") or "").lower()
        if severity == "high":
            penalty += 12
        elif severity == "medium":
            penalty += 7
        else:
            penalty += 3
    return min(penalty, 25)


def _risk_level_from_counts(counts: Dict[str, int]) -> str:
    if counts.get("high", 0) >= 2:
        return "high"
    if counts.get("high", 0) >= 1 or counts.get("medium", 0) >= 2:
        return "medium"
    return "low"


def _score_to_confidence(score: float) -> str:
    if score >= 70:
        return "high"
    if score >= 45:
        return "medium"
    return "low"
