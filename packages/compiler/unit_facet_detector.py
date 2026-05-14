"""Unit-based physical facet detection for parameter grouping.

This module only detects SI/engineering quantity families from units and
dimension markers. It intentionally avoids enumerating product-specific
parameter names.
"""

from __future__ import annotations

import re
from typing import Any

UNIT_TO_FACET = {
    "c": "temperature",
    "°c": "temperature",
    "℃": "temperature",
    "f": "temperature",
    "°f": "temperature",
    "℉": "temperature",
    "pa": "pressure",
    "kpa": "pressure",
    "mpa": "pressure",
    "bar": "pressure",
    "psi": "pressure",
    "psia": "pressure",
    "psig": "pressure",
    "psid": "pressure_differential",
    "a": "current",
    "ma": "current",
    "ka": "current",
    "v": "voltage",
    "kv": "voltage",
    "hz": "frequency",
    "gpm": "flow",
    "l/s": "flow",
    "m3/h": "flow",
    "m³/h": "flow",
    "cfm": "flow",
    "w": "power",
    "kw": "power",
    "mw": "power",
    "hp": "power",
    "%": "ratio",
    "minute": "time",
    "minutes": "time",
    "min": "time",
    "second": "time",
    "seconds": "time",
    "sec": "time",
    "s": "time",
    "分钟": "time",
    "秒": "time",
}

DIFFERENTIAL_PRESSURE_PATTERNS = [
    "压差",
    "差压",
    "differential pressure",
    "pressure differential",
    "psid",
    "Δp",
    "∆p",
]

UNIT_RE = re.compile(
    r"[-+]?\d+(?:\.\d+)?\s*([a-zA-Z°℃℉%]+(?:/[a-zA-Z]+)?|m[³3]/h|分钟|秒)"
)


def _normalize_unit(unit: Any) -> str:
    return str(unit or "").strip().replace(" ", "").lower()


def _lookup_unit(unit: Any) -> str | None:
    normalized = _normalize_unit(unit)
    if not normalized:
        return None
    return UNIT_TO_FACET.get(normalized)


def _has_pressure_differential_marker(text: str) -> bool:
    lower = text.lower()
    return any(pattern in lower for pattern in DIFFERENTIAL_PRESSURE_PATTERNS)


def _facet_from_text_units(text: str) -> str | None:
    for match in UNIT_RE.finditer(text):
        facet = _lookup_unit(match.group(1))
        if facet:
            return facet
    return None


def detect_unit_facet(parameter_name: str, structured_payload: dict[str, Any] | None = None) -> str | None:
    """Return a physical quantity facet inferred from units, or None.

    Known pressure units are promoted to ``pressure_differential`` when the
    name/value text explicitly carries a differential-pressure marker.
    """

    payload = structured_payload or {}
    text_parts = [parameter_name]
    for key in (
        "title",
        "summary",
        "description",
        "evidence_quote",
        "value",
        "default_value",
        "range_min",
        "range_max",
        "value_summary",
    ):
        value = payload.get(key)
        if value is not None:
            text_parts.append(str(value))
    combined_text = " ".join(text_parts)

    facet = _lookup_unit(payload.get("unit"))
    if facet == "pressure" and _has_pressure_differential_marker(combined_text):
        return "pressure_differential"
    if facet:
        return facet

    facet = _facet_from_text_units(combined_text)
    if facet == "pressure" and _has_pressure_differential_marker(combined_text):
        return "pressure_differential"
    if facet:
        return facet

    if _has_pressure_differential_marker(combined_text):
        return "pressure_differential"
    return None
