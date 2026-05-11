"""Authority arbitration — resolve value conflicts using doc 24 §11.3 rules.

Implements the 6 arbitration rules that determine which source's value takes
precedence when multiple authority layers disagree on a KO's value.
"""

from __future__ import annotations

from typing import Any

AUTHORITY_RANK = {
    "field_observation": 6,
    "industry_standard": 5,
    "regulatory_code": 4,
    "oem_manual": 3,
    "vendor_application_note": 2,
    "academic_reference": 1,
    "internal_sop": 0,
    "unspecified": -1,
}


def _rank(level: str) -> int:
    return AUTHORITY_RANK.get(level, -1)


def _layer_by_level(layers: list[dict[str, Any]], level: str) -> list[dict[str, Any]]:
    return [layer for layer in layers if layer.get("authority_level") == level]


def arbitrate(layers: list[dict[str, Any]], *, field_sample_count: int = 5) -> dict[str, Any]:
    """Apply the 6 authority arbitration rules to pick a recommended value.

    Args:
        layers: Authority layers from a KO's authority_summary_json.
        field_sample_count: Minimum field observation sample count for Rule 1
            (default 5, per doc 24 §10 O6).

    Returns:
        Dict with: recommended_value, recommended_authority_level,
        arbitration_reason, arbitration_rule_applied, field_sample_count.
    """
    if not layers:
        return {
            "recommended_value": None,
            "recommended_authority_level": None,
            "arbitration_reason": "No authority layers to arbitrate",
            "arbitration_rule_applied": None,
        }

    # Only one layer — no arbitration needed
    if len(layers) == 1:
        return {
            "recommended_value": layers[0].get("value_summary"),
            "recommended_authority_level": layers[0].get("authority_level"),
            "arbitration_reason": "Single source, no conflict to arbitrate",
            "arbitration_rule_applied": None,
        }

    sorted_layers = sorted(layers, key=lambda l: _rank(l.get("authority_level", "unspecified")), reverse=True)

    # Rule 1: field_observation w/ ≥N samples overrides all
    field_layers = _layer_by_level(sorted_layers, "field_observation")
    if field_layers:
        field_layer = field_layers[0]
        field_samples = field_layer.get("sample_count") or field_layer.get("evidence_count") or 0
        if field_samples >= field_sample_count:
            return {
                "recommended_value": field_layer.get("value_summary"),
                "recommended_authority_level": "field_observation",
                "arbitration_reason": (
                    f"Rule 1: field_observation with {field_samples} samples "
                    f"(≥{field_sample_count}) overrides all other sources"
                ),
                "arbitration_rule_applied": "rule_1_field_observation",
                "field_sample_count": field_samples,
            }

    # Rule 2: newer industry_standard overrides older industry_standard
    std_layers = _layer_by_level(sorted_layers, "industry_standard")
    if len(std_layers) >= 2:
        newest = None
        newest_year = 0
        for layer in std_layers:
            year = layer.get("publication_year") or 0
            if year > newest_year:
                newest_year = year
                newest = layer
        if newest and newest_year > 0:
            older = [l for l in std_layers if l != newest and (l.get("publication_year") or 0) < newest_year]
            if older:
                return {
                    "recommended_value": newest.get("value_summary"),
                    "recommended_authority_level": "industry_standard",
                    "arbitration_reason": (
                        f"Rule 2: newer industry_standard ({newest_year}) "
                        f"overrides older ({older[0].get('publication_year')})"
                    ),
                    "arbitration_rule_applied": "rule_2_newer_standard",
                }

    # Rule 3: industry_standard overrides oem_manual
    if std_layers:
        oem_layers = _layer_by_level(sorted_layers, "oem_manual")
        if oem_layers:
            return {
                "recommended_value": std_layers[0].get("value_summary"),
                "recommended_authority_level": "industry_standard",
                "arbitration_reason": "Rule 3: industry_standard overrides oem_manual",
                "arbitration_rule_applied": "rule_3_standard_over_oem",
            }

    # Rule 4: same-vendor newer oem_manual overrides older
    oem_layers = _layer_by_level(sorted_layers, "oem_manual")
    if len(oem_layers) >= 2:
        for i, layer_a in enumerate(oem_layers):
            for layer_b in oem_layers[i + 1:]:
                if layer_a.get("publisher") == layer_b.get("publisher"):
                    year_a = layer_a.get("publication_year") or 0
                    year_b = layer_b.get("publication_year") or 0
                    if year_a != year_b:
                        newer = layer_a if year_a > year_b else layer_b
                        older = layer_b if year_a > year_b else layer_a
                        return {
                            "recommended_value": newer.get("value_summary"),
                            "recommended_authority_level": "oem_manual",
                            "arbitration_reason": (
                                f"Rule 4: newer {newer.get('publisher')} manual "
                                f"({max(year_a, year_b)}) overrides older ({min(year_a, year_b)})"
                            ),
                            "arbitration_rule_applied": "rule_4_newer_oem",
                        }

    # Rule 5: oem_manual overrides vendor_application_note
    if oem_layers:
        vendor_layers = _layer_by_level(sorted_layers, "vendor_application_note")
        if vendor_layers:
            return {
                "recommended_value": oem_layers[0].get("value_summary"),
                "recommended_authority_level": "oem_manual",
                "arbitration_reason": "Rule 5: oem_manual overrides vendor_application_note",
                "arbitration_rule_applied": "rule_5_oem_over_vendor_note",
            }

    # Rule 6: authority ≥ oem_manual overrides academic_reference
    academic_layers = _layer_by_level(sorted_layers, "academic_reference")
    if academic_layers:
        higher = [l for l in sorted_layers if _rank(l.get("authority_level", "")) >= _rank("oem_manual")]
        if higher:
            return {
                "recommended_value": higher[0].get("value_summary"),
                "recommended_authority_level": higher[0].get("authority_level"),
                "arbitration_reason": "Rule 6: authority ≥ oem_manual overrides academic_reference",
                "arbitration_rule_applied": "rule_6_authority_over_academic",
            }

    # No rule matched — return highest-rank value
    return {
        "recommended_value": sorted_layers[0].get("value_summary"),
        "recommended_authority_level": sorted_layers[0].get("authority_level"),
        "arbitration_reason": (
            f"No specific arbitration rule matched. "
            f"Using highest-ranked source: {sorted_layers[0].get('authority_level')}"
        ),
        "arbitration_rule_applied": "fallback_highest_rank",
    }
