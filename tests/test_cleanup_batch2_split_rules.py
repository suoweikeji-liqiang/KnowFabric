"""Rule tests for over-merge cleanup batch 2."""

from __future__ import annotations

from scripts.cleanup_over_merge_batch2 import classify_evidence_group


def test_batch2_fault_code_classifier_splits_fc_numbers():
    evidence = {"evidence_text": "FC #13 Equation: SAT AVG > SAT SP-C", "page_no": 168}

    group = classify_evidence_group("ko_0aa1d7491394e13d", evidence)

    assert group.key == "fc_13"
    assert group.title == "AFDD Fault Condition FC#13"
    assert group.review_status == "published"


def test_batch2_classifier_routes_cross_topic_evidence_to_rejected_group():
    evidence = {"evidence_text": "表 3-3 冷却水水质 PH 6.5-8.0 氯离子 <200", "page_no": 12}

    group = classify_evidence_group("ko_0a2c2eebadb6cf7a", evidence)

    assert group.key == "rejected_water_quality"
    assert group.review_status == "rejected"
