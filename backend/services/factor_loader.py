"""Loads the read-only emission factor library from JSON datasets.

Factors live in backend/data/emission_factors/ and are kept separate from
application logic. End users cannot edit them through the API.
"""
import json
import os
from functools import lru_cache
from typing import List, Optional

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "emission_factors")


def _load_json(filename: str) -> dict:
    with open(os.path.join(_DATA_DIR, filename), "r", encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def load_all_raw() -> dict:
    """Return the raw merged JSON content of all factor datasets."""
    return {
        "clinker": _load_json("clinker_factors.json"),
        "fuel": _load_json("fuel_factors.json"),
        "general": _load_json("factors.json"),
        "scope3": _load_json("scope3_factors.json"),
    }


@lru_cache(maxsize=1)
def flatten_factors() -> List[dict]:
    """Flatten every dataset into a uniform list of factor records.

    Each record: {category, sub_category, factor_value, unit, source, year,
    applicable_facility_types, notes, editable, id}. Built-in records are
    read-only (editable=False); user-added factors are merged separately.
    """
    raw = load_all_raw()
    out: List[dict] = []

    # Clinker factors (single "factors" array under a top-level category).
    for f in raw["clinker"].get("factors", []):
        out.append(_normalize("clinker_process", f))

    # Fuel: kiln_fuel under "factors", plus mobile_equipment array.
    for f in raw["fuel"].get("factors", []):
        out.append(_normalize("kiln_fuel", f))
    for f in raw["fuel"].get("mobile_equipment", []):
        out.append(_normalize("mobile_equipment", f))

    # General + Scope 3: each key is a category mapping to a list.
    for dataset in ("general", "scope3"):
        for category, items in raw[dataset].items():
            if not isinstance(items, list):
                continue  # skip "description"
            for f in items:
                out.append(_normalize(category, f))

    return out


def _normalize(category: str, f: dict) -> dict:
    return {
        "id": None,
        "category": category,
        "sub_category": f.get("sub_category"),
        "factor_value": f.get("factor_value"),
        "unit": f.get("unit"),
        "scope": f.get("scope"),
        "source": f.get("source"),
        "year": f.get("year"),
        "applicable_facility_types": f.get("applicable_facility_types", []),
        "notes": f.get("notes"),
        "editable": False,
    }


def query_factors(
    category: Optional[str] = None,
    search: Optional[str] = None,
    facility_type: Optional[str] = None,
) -> List[dict]:
    """Filter the flattened factor library."""
    results = flatten_factors()
    if category:
        results = [f for f in results if f["category"] == category]
    if facility_type:
        results = [f for f in results if facility_type in (f["applicable_facility_types"] or [])]
    if search:
        needle = search.lower()
        results = [
            f
            for f in results
            if needle in (f["category"] or "").lower()
            or needle in (f["sub_category"] or "").lower()
            or needle in (f["source"] or "").lower()
        ]
    return results


def list_categories() -> List[str]:
    return sorted({f["category"] for f in flatten_factors()})
