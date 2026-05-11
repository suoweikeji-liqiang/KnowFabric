"""Tests for authority arbitration rules."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.authority_arbitration import arbitrate


def _layer(level: str, value: str, **kwargs) -> dict:
    result = {"authority_level": level, "value_summary": value}
    result.update(kwargs)
    return result


def test_single_layer_no_arbitration():
    result = arbitrate([_layer("oem_manual", "44F")])
    assert result["recommended_value"] == "44F"
    assert result["arbitration_rule_applied"] is None


def test_empty_layers():
    result = arbitrate([])
    assert result["recommended_value"] is None


def test_rule1_field_observation_overrides():
    result = arbitrate([
        _layer("industry_standard", "44F"),
        _layer("oem_manual", "42F"),
        _layer("field_observation", "43F", sample_count=5),
    ])
    assert result["arbitration_rule_applied"] == "rule_1_field_observation"
    assert result["recommended_value"] == "43F"


def test_rule1_field_observation_insufficient_samples():
    result = arbitrate([
        _layer("industry_standard", "44F"),
        _layer("field_observation", "43F", sample_count=3),
    ])
    assert result["arbitration_rule_applied"] != "rule_1_field_observation"


def test_rule2_newer_standard_overrides():
    result = arbitrate([
        _layer("industry_standard", "44F", publication_year=2022),
        _layer("industry_standard", "42F", publication_year=2019),
    ])
    assert result["arbitration_rule_applied"] == "rule_2_newer_standard"
    assert result["recommended_value"] == "44F"


def test_rule3_standard_overrides_oem():
    result = arbitrate([
        _layer("oem_manual", "42F"),
        _layer("industry_standard", "44F"),
    ])
    assert result["arbitration_rule_applied"] == "rule_3_standard_over_oem"
    assert result["recommended_value"] == "44F"


def test_rule4_newer_oem_same_vendor():
    result = arbitrate([
        _layer("oem_manual", "42F", publisher="Trane", publication_year=2018),
        _layer("oem_manual", "44F", publisher="Trane", publication_year=2023),
    ])
    assert result["arbitration_rule_applied"] == "rule_4_newer_oem"
    assert result["recommended_value"] == "44F"


def test_rule5_oem_over_vendor_note():
    result = arbitrate([
        _layer("vendor_application_note", "40F"),
        _layer("oem_manual", "44F"),
    ])
    assert result["arbitration_rule_applied"] == "rule_5_oem_over_vendor_note"
    assert result["recommended_value"] == "44F"


def test_rule6_authority_over_academic():
    result = arbitrate([
        _layer("academic_reference", "50F"),
        _layer("oem_manual", "44F"),
    ])
    assert result["arbitration_rule_applied"] == "rule_6_authority_over_academic"
    assert result["recommended_value"] == "44F"


def test_fallback_highest_rank_when_no_rule_matches():
    result = arbitrate([
        _layer("vendor_application_note", "40F"),
        _layer("vendor_application_note", "42F"),
    ])
    assert result["arbitration_rule_applied"] == "fallback_highest_rank"
    assert result["recommended_value"] in ("40F", "42F")


if __name__ == "__main__":
    test_single_layer_no_arbitration()
    test_empty_layers()
    test_rule1_field_observation_overrides()
    test_rule1_field_observation_insufficient_samples()
    test_rule2_newer_standard_overrides()
    test_rule3_standard_overrides_oem()
    test_rule4_newer_oem_same_vendor()
    test_rule5_oem_over_vendor_note()
    test_rule6_authority_over_academic()
    test_fallback_highest_rank_when_no_rule_matches()
    print("Authority arbitration tests passed")
