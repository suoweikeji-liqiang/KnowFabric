"""Tests for expanded health checks."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.health.checks import (
    build_full_health_report,
    detect_anchor_quality_issues,
    detect_applicability_ambiguity,
    detect_ko_conflicts,
    detect_terminology_drift,
)


def _ko(knowledge_object_id, ontology_class_id="centrifugal_chiller",
        knowledge_object_type="parameter_spec", canonical_key=None,
        title="Test", parameter_name=None, value=None, default_value=None,
        applicability=None):
    return {
        "knowledge_object_id": knowledge_object_id,
        "ontology_class_id": ontology_class_id,
        "knowledge_object_type": knowledge_object_type,
        "canonical_key": canonical_key or f"key_{knowledge_object_id}",
        "title": title,
        "structured_payload_json": {
            "parameter_name": parameter_name or title,
            "value": value,
            "default_value": default_value,
        },
        "applicability_json": applicability or {},
    }


def _evidence(knowledge_object_id, evidence_text):
    return {"knowledge_object_id": knowledge_object_id, "evidence_text": evidence_text}


def test_conflict_detection_flags_similar_names_different_values():
    kos = [
        _ko("ko_a", canonical_key="chw_setpoint", title="chilled water setpoint", value="44F"),
        _ko("ko_b", canonical_key="chw_temp", title="chilled water supply temperature", value="50F"),
    ]
    findings = detect_ko_conflicts(kos)
    assert len(findings) == 1
    assert findings[0]["code"] == "ko_conflict"
    assert findings[0]["ko_a"] == "ko_a"
    assert findings[0]["ko_b"] == "ko_b"


def test_conflict_detection_skips_same_value():
    kos = [
        _ko("ko_a", canonical_key="a", title="CHWS Setpoint", value="44F"),
        _ko("ko_b", canonical_key="b", title="CHW Supply Temp", value="44F"),
    ]
    findings = detect_ko_conflicts(kos)
    assert len(findings) == 0


def test_conflict_detection_skips_different_types():
    kos = [
        _ko("ko_a", knowledge_object_type="parameter_spec", title="Setpoint", value="44F"),
        _ko("ko_b", knowledge_object_type="maintenance_procedure", title="Setpoint", value="50F"),
    ]
    findings = detect_ko_conflicts(kos)
    assert len(findings) == 0


def test_terminology_drift_detects_similar_names():
    kos = [
        _ko("ko_a", canonical_key="chw_supply_temp", parameter_name="chilled_water_supply_temperature"),
        _ko("ko_b", canonical_key="chw_leaving_temp", parameter_name="chilled_water_leaving_temperature"),
    ]
    findings = detect_terminology_drift(kos)
    assert len(findings) >= 1
    assert findings[0]["code"] == "terminology_drift"


def test_terminology_drift_skips_dissimilar():
    kos = [
        _ko("ko_a", parameter_name="chilled_water_setpoint"),
        _ko("ko_b", parameter_name="cooling_capacity_rating"),
    ]
    findings = detect_terminology_drift(kos)
    assert len(findings) == 0


def test_applicability_ambiguity_from_evidence():
    kos = [
        _ko("ko_a", applicability={}),
    ]
    evidence = [
        _evidence("ko_a", "The Trane CVGF chiller requires 44F setpoint at standard conditions"),
    ]
    findings = detect_applicability_ambiguity(kos, evidence_rows=evidence)
    assert len(findings) == 1
    assert findings[0]["code"] == "applicability_ambiguity"
    assert "Trane" in findings[0]["potential_brands_in_evidence"]


def test_applicability_ambiguity_skips_when_brand_present():
    kos = [
        _ko("ko_a", applicability={"brand": "Trane"}),
    ]
    evidence = [_evidence("ko_a", "The Trane chiller...")]
    findings = detect_applicability_ambiguity(kos, evidence_rows=evidence)
    assert len(findings) == 0


def test_anchor_quality_flags_weak_anchors():
    kos = [
        _ko("ko_a", ontology_class_id="centrifugal_chiller"),
    ]
    evidence = [
        _evidence("ko_a", "This variable frequency drive requires 50Hz input"),
    ]
    findings = detect_anchor_quality_issues(kos, evidence_rows=evidence)
    assert len(findings) == 1
    assert findings[0]["code"] == "anchor_quality"
    assert findings[0]["match_ratio"] < 0.5


def test_anchor_quality_passes_strong_anchors():
    kos = [
        _ko("ko_a", ontology_class_id="centrifugal_chiller"),
    ]
    evidence = [
        _evidence("ko_a", "The centrifugal chiller requires 44F chilled water setpoint"),
    ]
    findings = detect_anchor_quality_issues(kos, evidence_rows=evidence)
    assert len(findings) == 0


def test_full_health_report():
    kos = [
        _ko("ko_a", canonical_key="a", title="chilled water setpoint", value="44F"),
        _ko("ko_b", canonical_key="b", title="chilled water supply temperature", value="50F"),
        _ko("ko_c", applicability={}),
    ]
    evidence = [
        _evidence("ko_a", "The Trane centrifugal chiller setpoint is 44F"),
        _evidence("ko_b", "Set chiller leaving water temperature to 50F"),
        _evidence("ko_c", "Configured on Carrier 19XR chiller at 7C"),
    ]
    report = build_full_health_report(kos, evidence_rows=evidence)
    assert report["health_mode"] == "full_health_report"
    assert report["summary"]["total_findings"] >= 2
    assert "ko_conflict" in report["summary"]["by_code"]
    assert "applicability_ambiguity" in report["summary"]["by_code"]
