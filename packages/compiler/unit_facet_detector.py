"""Unit-based physical facet detection for parameter grouping.

This module only detects SI/engineering quantity families from units and
dimension markers. It intentionally avoids enumerating product-specific
parameter names.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

BRICK_FACET_MAP_PATH = (
    Path(__file__).resolve().parents[2]
    / "domain_packages"
    / "hvac"
    / "v2"
    / "brick_facet_map.yaml"
)

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


def _payload_text(parameter_name: str, payload: dict[str, Any]) -> str:
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
    return " ".join(text_parts)


def _facet_from_text_units(text: str) -> str | None:
    for match in UNIT_RE.finditer(text):
        facet = _lookup_unit(match.group(1))
        if facet:
            return facet
    return None


@lru_cache(maxsize=1)
def _load_brick_reference_points() -> list[dict[str, Any]]:
    if not BRICK_FACET_MAP_PATH.exists():
        return []
    data = yaml.safe_load(BRICK_FACET_MAP_PATH.read_text(encoding="utf-8")) or {}
    points = data.get("brick_reference_points") or {}
    loaded: list[dict[str, Any]] = []
    for tag, config in points.items():
        if not isinstance(config, dict):
            continue
        subtype = str(config.get("facet_subtype") or "").strip()
        keywords = [str(k).strip().lower() for k in config.get("keywords") or [] if str(k).strip()]
        if subtype and keywords:
            loaded.append({"tag": tag, "subtype": subtype, "keywords": keywords})
    loaded.sort(key=lambda item: max(len(k) for k in item["keywords"]), reverse=True)
    return loaded


def detect_brick_subtype(parameter_name: str, structured_payload: dict[str, Any] | None = None) -> str | None:
    """Detect a Brick reference-point subtype from name and payload text."""

    text = _payload_text(parameter_name, structured_payload or {}).lower()
    for point in _load_brick_reference_points():
        if any(keyword in text for keyword in point["keywords"]):
            return str(point["subtype"])
    return None


def detect_unit_facet(parameter_name: str, structured_payload: dict[str, Any] | None = None) -> str | None:
    """Return a physical quantity facet inferred from units, or None.

    Known pressure units are promoted to ``pressure_differential`` when the
    name/value text explicitly carries a differential-pressure marker.
    """

    payload = structured_payload or {}
    combined_text = _payload_text(parameter_name, payload)

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


def detect_facet_v2(
    parameter_name: str,
    structured_payload: dict[str, Any] | None = None,
) -> tuple[str | None, str | None]:
    """Return physical quantity and Brick reference-point subtype."""

    payload = structured_payload or {}
    return detect_unit_facet(parameter_name, payload), detect_brick_subtype(parameter_name, payload)
