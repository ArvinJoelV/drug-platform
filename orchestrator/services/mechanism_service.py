from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


_MECHANISM_CACHE: dict[str, Dict[str, Any]] = {}

_CURATED_MECHANISMS: dict[str, Dict[str, Any]] = {
    "metformin": {
        "primary_target": "AMPK",
        "primary_action": "activation",
        "targets": [
            {"name": "AMPK", "action": "activation", "confidence": 0.92},
            {"name": "mTOR", "action": "indirect inhibition", "confidence": 0.66},
            {"name": "Mitochondrial Complex I", "action": "inhibition", "confidence": 0.7},
        ],
        "mechanism_class": "metabolic modulator",
        "pathways": ["AMPK signaling", "mTOR signaling", "glucose metabolism"],
        "query_terms": ["AMPK", "activation", "mTOR", "glucose metabolism"],
        "confidence": 0.86,
        "source": "curated_lookup",
    },
    "bevacizumab": {
        "primary_target": "VEGF",
        "primary_action": "inhibition",
        "targets": [
            {"name": "VEGF", "action": "inhibition", "confidence": 0.97},
        ],
        "mechanism_class": "anti-angiogenic monoclonal antibody",
        "pathways": ["VEGF signaling", "angiogenesis"],
        "query_terms": ["VEGF", "inhibition", "angiogenesis"],
        "confidence": 0.95,
        "source": "curated_lookup",
    },
    "sunitinib": {
        "primary_target": "VEGFR",
        "primary_action": "inhibition",
        "targets": [
            {"name": "VEGFR", "action": "inhibition", "confidence": 0.92},
            {"name": "PDGFR", "action": "inhibition", "confidence": 0.84},
            {"name": "KIT", "action": "inhibition", "confidence": 0.81},
        ],
        "mechanism_class": "multi-kinase inhibitor",
        "pathways": ["VEGF signaling", "PDGF signaling", "angiogenesis"],
        "query_terms": ["VEGFR", "inhibition", "angiogenesis", "PDGFR"],
        "confidence": 0.9,
        "source": "curated_lookup",
    },
    "sorafenib": {
        "primary_target": "VEGFR",
        "primary_action": "inhibition",
        "targets": [
            {"name": "VEGFR", "action": "inhibition", "confidence": 0.88},
            {"name": "RAF", "action": "inhibition", "confidence": 0.85},
            {"name": "PDGFR", "action": "inhibition", "confidence": 0.77},
        ],
        "mechanism_class": "multi-kinase inhibitor",
        "pathways": ["VEGF signaling", "MAPK signaling", "angiogenesis"],
        "query_terms": ["VEGFR", "RAF", "inhibition", "angiogenesis"],
        "confidence": 0.88,
        "source": "curated_lookup",
    },
    "aspirin": {
        "primary_target": "COX-1",
        "primary_action": "inhibition",
        "targets": [
            {"name": "COX-1", "action": "inhibition", "confidence": 0.96},
            {"name": "COX-2", "action": "inhibition", "confidence": 0.8},
        ],
        "mechanism_class": "cyclooxygenase inhibitor",
        "pathways": ["arachidonic acid metabolism", "platelet aggregation"],
        "query_terms": ["COX-1", "COX-2", "inhibition", "platelet aggregation"],
        "confidence": 0.91,
        "source": "curated_lookup",
    },
}


def resolve_mechanism_context(molecule: str) -> Dict[str, Any]:
    normalized = molecule.strip().lower()
    if normalized in _MECHANISM_CACHE:
        return deepcopy(_MECHANISM_CACHE[normalized])

    mechanism = deepcopy(_CURATED_MECHANISMS.get(normalized) or _fallback_mechanism_context(molecule))
    mechanism["molecule"] = molecule
    mechanism["resolved"] = bool(mechanism.get("primary_target"))

    _MECHANISM_CACHE[normalized] = mechanism
    return deepcopy(mechanism)


def _fallback_mechanism_context(molecule: str) -> Dict[str, Any]:
    return {
        "primary_target": "",
        "primary_action": "",
        "targets": [],
        "mechanism_class": "unknown",
        "pathways": [],
        "query_terms": [],
        "confidence": 0.2,
        "source": "fallback_unknown",
        "notes": f"No curated mechanism match was found for {molecule}.",
    }
