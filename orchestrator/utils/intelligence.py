from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable, List


def build_intelligence_payload(aggregated_report: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    normalized = normalize_signals(state)
    insights = build_cross_domain_insights(normalized)
    confidence = build_confidence_breakdown(normalized, insights)
    opportunities = rank_opportunities(normalized, insights, confidence)

    return {
        "normalized_signals": normalized,
        "cross_domain_insights": insights,
        "confidence_breakdown": confidence,
        "top_opportunities": opportunities,
        "summary_basis": {
            "molecule": aggregated_report.get("molecule"),
            "sources_used": aggregated_report.get("meta", {}).get("sources_used", []),
        },
    }


def normalize_signals(state: Dict[str, Any]) -> Dict[str, Any]:
    clinical_data = state.get("clinical_data") or {}
    literature_data = state.get("literature_data") or {}
    patent_data = state.get("patent_data") or {}
    regulatory_data = state.get("regulatory_data") or {}
    market_data = state.get("market_data") or {}
    mechanism_context = state.get("mechanism_context") or {}

    trials = clinical_data.get("trials", []) or []
    findings = literature_data.get("findings", []) or []
    regulatory_core = regulatory_data.get("data", {}) if isinstance(regulatory_data.get("data"), dict) else {}

    clinical_diseases = Counter()
    trial_phases = Counter()
    for trial in trials:
        condition = _clean_value(trial.get("condition"))
        if condition:
            clinical_diseases[condition] += 1
        phase = _clean_value(trial.get("phase"))
        if phase:
            trial_phases[phase] += 1

    literature_diseases = Counter()
    mechanisms = Counter()
    sentiments = Counter()
    for finding in findings:
        for disease in finding.get("disease_associations", []) or []:
            cleaned = _clean_value(disease)
            if cleaned:
                literature_diseases[cleaned] += 1
        for mechanism in finding.get("mechanisms", []) or []:
            cleaned = _clean_value(mechanism)
            if cleaned:
                mechanisms[cleaned] += 1
        sentiment = _clean_value(finding.get("sentiment"))
        if sentiment:
            sentiments[sentiment] += 1

    approved_indications = [
        _clean_value(item)
        for item in regulatory_core.get("approved_indications", []) or []
        if _clean_value(item)
    ]

    return {
        "mechanism": {
            "primary_target": _clean_value(mechanism_context.get("primary_target")),
            "primary_action": _clean_value(mechanism_context.get("primary_action")),
            "targets": mechanism_context.get("targets", []) or [],
            "pathways": mechanism_context.get("pathways", []) or [],
            "confidence": mechanism_context.get("confidence", 0.0),
            "query_terms": mechanism_context.get("query_terms", []) or [],
        },
        "clinical": {
            "diseases": _counter_to_ranked_list(clinical_diseases),
            "trial_strength": len(trials),
            "phases": dict(trial_phases),
            "statuses": clinical_data.get("summary", {}).get("statuses", {}),
        },
        "literature": {
            "diseases": _counter_to_ranked_list(literature_diseases),
            "mechanisms": _counter_to_ranked_list(mechanisms),
            "sentiment": dict(sentiments),
            "papers_analyzed": literature_data.get("papers_analyzed", 0),
        },
        "patent": {
            "freedom_to_operate": patent_data.get("commercial_freedom")
            or patent_data.get("detailed_analysis", {}).get("repurposing_feasibility", {}).get("freedom_to_operate")
            or "Unknown",
            "risk": patent_data.get("detailed_analysis", {}).get("risk_factors", []) or [],
        },
        "regulatory": {
            "approved": approved_indications,
            "risks": regulatory_core.get("contradictions", []) or [],
            "warnings": regulatory_core.get("warnings", []) or [],
            "confidence": regulatory_core.get("confidence", 0),
        },
        "market": {
            "disease": _clean_value(market_data.get("disease")),
            "market_score": _map_market_score(market_data.get("market_potential")),
            "market_potential": market_data.get("market_potential", "Unknown"),
            "market_stats": market_data.get("detailed_analysis", {}).get("key_statistics", []) or [],
        },
    }


def build_cross_domain_insights(normalized: Dict[str, Any]) -> List[Dict[str, Any]]:
    clinical_map = _ranked_list_to_map(normalized["clinical"]["diseases"])
    literature_map = _ranked_list_to_map(normalized["literature"]["diseases"])
    candidate_diseases = set(clinical_map) | set(literature_map)
    approved_text = " ".join(normalized["regulatory"]["approved"]).lower()
    market_disease = (normalized["market"].get("disease") or "").lower()

    insights: List[Dict[str, Any]] = []
    for disease in sorted(candidate_diseases):
        supporting_domains = []
        missing_domains = []
        risk_flags = []
        evidence_parts = []

        clinical_hits = clinical_map.get(disease, 0)
        literature_hits = literature_map.get(disease, 0)
        if clinical_hits:
            supporting_domains.append("clinical")
            evidence_parts.append(f"{clinical_hits} clinical signal(s)")
        else:
            missing_domains.append("clinical")

        if literature_hits:
            supporting_domains.append("literature")
            evidence_parts.append(f"{literature_hits} literature signal(s)")
        else:
            missing_domains.append("literature")

        if market_disease and (disease.lower() in market_disease or market_disease in disease.lower()):
            supporting_domains.append("market")
            evidence_parts.append(f"market aligned to {normalized['market'].get('disease')}")
        else:
            missing_domains.append("market")

        if disease.lower() in approved_text:
            supporting_domains.append("regulatory")
            risk_flags.append("Already appears in approved indication text; novelty reduced.")
        else:
            missing_domains.append("regulatory")

        if normalized["patent"]["freedom_to_operate"] == "Low":
            risk_flags.append("Patent freedom-to-operate appears constrained.")
        if not clinical_hits and literature_hits:
            risk_flags.append("Literature-only disease signal needs clinical validation.")
        if clinical_hits and not literature_hits:
            risk_flags.append("Clinical activity exists without matching literature support.")
        if normalized["regulatory"]["risks"]:
            risk_flags.append("General regulatory contraindications should be checked against target population.")

        insights.append(
            {
                "disease": disease,
                "evidence_summary": "; ".join(evidence_parts) if evidence_parts else "Sparse cross-domain evidence",
                "supporting_domains": supporting_domains,
                "missing_domains": sorted(set(missing_domains)),
                "risk_flags": _unique_preserve_order(risk_flags),
            }
        )

    return insights


def build_confidence_breakdown(normalized: Dict[str, Any], insights: List[Dict[str, Any]]) -> Dict[str, Any]:
    clinical_map = _ranked_list_to_map(normalized["clinical"]["diseases"])
    literature_map = _ranked_list_to_map(normalized["literature"]["diseases"])
    market_score = normalized["market"]["market_score"]
    regulatory_penalty = 10 if normalized["regulatory"]["approved"] else 0
    regulatory_penalty += 5 if normalized["regulatory"]["risks"] else 0
    patent_penalty = 10 if normalized["patent"]["freedom_to_operate"] == "Low" else 0

    per_disease_scores = []
    numeric_scores = []
    for insight in insights:
        disease = insight["disease"]
        score = 0
        score += min(clinical_map.get(disease, 0) * 18, 45)
        score += min(literature_map.get(disease, 0) * 10, 25)
        score += market_score
        score += 8 if normalized["patent"]["freedom_to_operate"] in {"High", "Unknown"} else 0
        score -= regulatory_penalty
        score -= patent_penalty
        score -= min(len(insight.get("missing_domains", [])) * 4, 12)
        score = max(0, min(score, 100))
        numeric_scores.append(score)
        per_disease_scores.append(
            {
                "disease": disease,
                "score": score,
                "confidence": _score_to_confidence(score),
                "drivers": {
                    "clinical_weight": min(clinical_map.get(disease, 0) * 18, 45),
                    "literature_weight": min(literature_map.get(disease, 0) * 10, 25),
                    "market_weight": market_score,
                    "regulatory_penalty": regulatory_penalty,
                    "patent_penalty": patent_penalty,
                },
            }
        )

    global_score = round(sum(numeric_scores) / len(numeric_scores), 2) if numeric_scores else 0.0
    return {
        "per_disease_scores": sorted(per_disease_scores, key=lambda item: item["score"], reverse=True),
        "global_score": global_score,
        "global_confidence": _score_to_confidence(global_score),
        "scoring_policy": {
            "priority_order": ["clinical", "literature", "market", "patent"],
            "regulatory_mode": "penalty",
        },
    }


def rank_opportunities(
    normalized: Dict[str, Any],
    insights: List[Dict[str, Any]],
    confidence_breakdown: Dict[str, Any],
) -> List[Dict[str, Any]]:
    score_lookup = {
        item["disease"]: item for item in confidence_breakdown.get("per_disease_scores", [])
    }
    approved_text = " ".join(normalized["regulatory"]["approved"]).lower()

    ranked = []
    for insight in insights:
        disease = insight["disease"]
        base = score_lookup.get(disease, {"score": 0, "confidence": "low"})
        novelty_bonus = 12 if disease.lower() not in approved_text else -15
        risk_penalty = min(len(insight.get("risk_flags", [])) * 3, 12)
        final_score = max(0, min(base["score"] + novelty_bonus - risk_penalty, 100))
        ranked.append(
            {
                "disease": disease,
                "score": final_score,
                "confidence": base.get("confidence", "low"),
                "rationale": (
                    f"{disease} combines {', '.join(insight.get('supporting_domains', []) or ['limited evidence'])} "
                    f"signals with {len(insight.get('missing_domains', []))} missing domain(s)."
                ),
                "signals_used": insight.get("supporting_domains", []),
                "novelty": "novel" if disease.lower() not in approved_text else "already_approved_or_adjacent",
            }
        )

    return sorted(ranked, key=lambda item: item["score"], reverse=True)[:5]


def build_posthoc_regulatory_check(intelligence: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    regulatory_data = state.get("regulatory_data") or {}
    regulatory_core = regulatory_data.get("data", {}) if isinstance(regulatory_data.get("data"), dict) else {}
    approved_text = " ".join(regulatory_core.get("approved_indications", []) or []).lower()
    contradictions = regulatory_core.get("contradictions", []) or []
    warnings = regulatory_core.get("warnings", []) or []

    checks = []
    for candidate in intelligence.get("top_opportunities", [])[:3]:
        disease = candidate.get("disease", "")
        checks.append(
            {
                "disease": disease,
                "approval_overlap": disease.lower() in approved_text if disease else False,
                "contraindication_count": len(contradictions),
                "warning_count": len(warnings),
                "summary": (
                    "Already overlaps approved labeling text."
                    if disease and disease.lower() in approved_text
                    else "No direct overlap found in approved indication text; review contraindications for target population fit."
                ),
            }
        )

    return {"checked_candidates": checks}


def _counter_to_ranked_list(counter: Counter) -> List[Dict[str, Any]]:
    return [{"name": name, "count": count} for name, count in counter.most_common()]


def _ranked_list_to_map(items: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    return {item["name"]: int(item.get("count", 0)) for item in items if item.get("name")}


def _clean_value(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text in {"", "N/A", "Unknown", "None"}:
        return ""
    return text


def _map_market_score(value: Any) -> int:
    mapping = {"high": 15, "very high": 18, "medium": 8, "moderate": 8, "low": 3}
    return mapping.get(str(value).strip().lower(), 5 if value else 0)


def _score_to_confidence(score: float) -> str:
    if score >= 70:
        return "high"
    if score >= 45:
        return "medium"
    return "low"


def _unique_preserve_order(values: Iterable[str]) -> List[str]:
    seen = set()
    output = []
    for value in values:
        if value not in seen:
            seen.add(value)
            output.append(value)
    return output
