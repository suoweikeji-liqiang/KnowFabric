"""Tests for standard knowledge duplicate grouping helpers."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.dedupe_standard_knowledge import DedupeRow, duplicate_reason, group_duplicate_rows, has_conflicting_semantics, section_prefix


def test_section_prefix_compares_specific_rule_level() -> None:
    assert section_prefix("5.20.2.2.a") == "5.20.2.2"
    assert section_prefix("5.6") == "5.6"


def test_duplicate_reason_requires_same_section_prefix() -> None:
    left = row("ko_1", "5.20.2.2", "Plant Enable Logic")
    right = row("ko_2", "5.20.2.3", "Plant Enable Logic")

    assert duplicate_reason(left, right, 0.86) is None


def test_group_duplicate_rows_keeps_highest_trust_and_evidence() -> None:
    rows = [
        row("ko_l3", "5.20.2.2", "Chiller Plant Enable", trust_level="L3", evidence_count=1),
        row("ko_l4", "5.20.2.2", "Chiller Plant Enable Logic", trust_level="L4", evidence_count=2),
        row("ko_other", "5.20.2.3", "Chiller Plant Disable", trust_level="L3", evidence_count=1),
    ]

    groups = group_duplicate_rows(rows, 0.70)

    assert len(groups) == 1
    assert groups[0]["keep"]["knowledge_object_id"] == "ko_l4"
    assert groups[0]["duplicates"][0]["knowledge_object_id"] == "ko_l3"


def test_conflicting_semantics_prevent_false_duplicate_pairs() -> None:
    assert has_conflicting_semantics("Chiller Stage Up Efficiency", "Chiller Stage Down Efficiency")
    assert has_conflicting_semantics("Ventilation ASHRAE 62.1", "Ventilation Title 24")
    assert has_conflicting_semantics("Condensing Boiler Stage Up", "Non-Condensing Boiler Stage Up")
    assert has_conflicting_semantics("Low Airflow Alarm Level 3", "Low Airflow Alarm Level 4")
    assert has_conflicting_semantics("Cooling SAT Reset Request - 1 Request", "Cooling SAT Reset Request - 3 Requests")
    assert has_conflicting_semantics("AFDD FC#2: MAT Too Low", "AFDD FC#3: MAT Too High")
    assert has_conflicting_semantics("Low Airflow Alarm 70% of Setpoint", "Low Airflow Alarm 50% of Setpoint")


def row(
    knowledge_object_id: str,
    section_id: str,
    title: str,
    *,
    trust_level: str = "L3",
    evidence_count: int = 1,
) -> DedupeRow:
    return DedupeRow(
        knowledge_object_id=knowledge_object_id,
        domain_id="hvac",
        ontology_class_id="chiller",
        knowledge_object_type="operational_sequence",
        canonical_key=f"ashrae:g36:operational_sequence:{section_id.replace('.', '_')}:{title.lower().replace(' ', '_')}",
        title=title,
        summary=f"{title} summary",
        section_id=section_id,
        trust_level=trust_level,
        confidence_score=0.9,
        evidence_count=evidence_count,
        page_nos=(172,),
    )
