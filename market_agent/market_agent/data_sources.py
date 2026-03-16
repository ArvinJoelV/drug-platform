"""Data loading helpers for the Market Intelligence Agent prototype."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests


WHO_GHO_BASE_URL = "https://ghoapi.azureedge.net/api"
WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2"

DEFAULT_WHO_INDICATORS = [
    "GHED_CHEGDP_SHA2011",
    "GHED_CHE_pc_US_SHA2011",
]

DEFAULT_WORLD_BANK_INDICATORS = {
    "Current health expenditure (% of GDP)": "SH.XPD.CHEX.GD.ZS",
    "Current health expenditure per capita (current US$)": "SH.XPD.CHEX.PC.CD",
    "Population, total": "SP.POP.TOTL",
    "Life expectancy at birth, total (years)": "SP.DYN.LE00.IN",
}


def _safe_get_json(url: str, params: dict[str, Any] | None = None) -> Any:
    """Fetch JSON with a short timeout and a clear error message."""
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_who_gho_data(
    indicator_codes: list[str] | None = None,
    max_records_per_indicator: int = 50,
) -> list[dict[str, Any]]:
    """Fetch a small WHO Global Health Observatory sample for each indicator."""
    indicator_codes = indicator_codes or DEFAULT_WHO_INDICATORS
    records: list[dict[str, Any]] = []

    for indicator_code in indicator_codes:
        url = f"{WHO_GHO_BASE_URL}/{indicator_code}"
        payload = _safe_get_json(
            url,
            params={
                "$format": "json",
                "$top": max_records_per_indicator,
            },
        )

        for row in payload.get("value", []):
            records.append(
                {
                    "source": "WHO GHO",
                    "indicator_code": indicator_code,
                    "indicator_name": indicator_code,
                    "country": row.get("SpatialDim"),
                    "year": row.get("TimeDim"),
                    "value": row.get("NumericValue"),
                    "unit": row.get("Dim1"),
                    "raw": row,
                }
            )

    return records


def fetch_world_bank_indicators(
    indicator_map: dict[str, str] | None = None,
    countries: str = "all",
    years: int = 5,
    max_records_per_indicator: int = 200,
) -> list[dict[str, Any]]:
    """Fetch World Bank health and spending indicators in JSON format."""
    indicator_map = indicator_map or DEFAULT_WORLD_BANK_INDICATORS
    records: list[dict[str, Any]] = []

    for indicator_name, indicator_code in indicator_map.items():
        url = f"{WORLD_BANK_BASE_URL}/country/{countries}/indicator/{indicator_code}"
        payload = _safe_get_json(
            url,
            params={
                "format": "json",
                "per_page": max_records_per_indicator,
                "mrv": years,
            },
        )

        for row in payload[1] if isinstance(payload, list) and len(payload) > 1 else []:
            if row.get("value") is None:
                continue

            records.append(
                {
                    "source": "World Bank",
                    "indicator_code": indicator_code,
                    "indicator_name": indicator_name,
                    "country": (row.get("country") or {}).get("value"),
                    "year": row.get("date"),
                    "value": row.get("value"),
                    "unit": row.get("unit"),
                    "raw": row,
                }
            )

    return records


def load_local_prevalence_csv(csv_path: str, disease_name: str) -> list[dict[str, Any]]:
    """Load an optional local prevalence file and keep rows related to the disease."""
    dataframe = pd.read_csv(csv_path)
    normalized = dataframe.copy()
    normalized.columns = [column.strip().lower() for column in normalized.columns]

    text_view = normalized.astype(str).apply(
        lambda row: " ".join(value.lower() for value in row.values),
        axis=1,
    )
    mask = text_view.str.contains(disease_name.lower(), na=False)
    filtered = normalized[mask]

    records: list[dict[str, Any]] = []
    for row in filtered.to_dict(orient="records"):
        records.append(
            {
                "source": "Local CSV",
                "indicator_code": "local_prevalence",
                "indicator_name": "Local disease prevalence row",
                "country": row.get("country") or row.get("location"),
                "year": row.get("year"),
                "value": row.get("value") or row.get("prevalence") or row.get("incidence"),
                "unit": row.get("unit"),
                "raw": row,
            }
        )

    return records


def record_to_text(record: dict[str, Any], disease_name: str) -> str:
    """Convert a structured row into a retrieval-friendly text passage."""
    country = record.get("country") or "Global or unspecified geography"
    year = record.get("year") or "unknown year"
    value = record.get("value") if record.get("value") is not None else "not reported"
    unit = record.get("unit") or "unspecified unit"

    return (
        f"Disease: {disease_name}. "
        f"Source: {record.get('source')}. "
        f"Indicator: {record.get('indicator_name')} ({record.get('indicator_code')}). "
        f"Geography: {country}. "
        f"Year: {year}. "
        f"Value: {value}. "
        f"Unit or dimension: {unit}. "
        "Use this record as epidemiology or healthcare market context for market sizing."
    )


def build_documents(
    disease_name: str,
    prevalence_csv_path: str | None = None,
    who_indicator_codes: list[str] | None = None,
    world_bank_indicator_map: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Fetch raw data from sources and turn them into plain-text documents."""
    records: list[dict[str, Any]] = []

    try:
        records.extend(fetch_who_gho_data(indicator_codes=who_indicator_codes))
    except requests.RequestException as exc:
        records.append(
            {
                "source": "WHO GHO",
                "indicator_code": "fetch_error",
                "indicator_name": "WHO retrieval error",
                "country": None,
                "year": None,
                "value": None,
                "unit": None,
                "raw": {"error": str(exc)},
            }
        )

    try:
        records.extend(fetch_world_bank_indicators(indicator_map=world_bank_indicator_map))
    except requests.RequestException as exc:
        records.append(
            {
                "source": "World Bank",
                "indicator_code": "fetch_error",
                "indicator_name": "World Bank retrieval error",
                "country": None,
                "year": None,
                "value": None,
                "unit": None,
                "raw": {"error": str(exc)},
            }
        )

    if prevalence_csv_path:
        records.extend(load_local_prevalence_csv(prevalence_csv_path, disease_name))

    documents: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        metadata = {
            "source": record.get("source") or "Unknown source",
            "indicator_code": record.get("indicator_code") or "unknown_indicator",
            "indicator_name": record.get("indicator_name") or "Unknown indicator",
            "country": record.get("country") or "Unknown geography",
            "year": str(record.get("year") or "unknown_year"),
        }
        documents.append(
            {
                "id": f"doc-{index}",
                "text": record_to_text(record, disease_name),
                "metadata": metadata,
            }
        )

    return documents

