"""Tests for review-pack manual fixture construction helpers."""

from scripts.build_manual_fixture_from_review_candidates import _base_manual_entry


def test_base_manual_entry_preserves_curated_publisher_metadata() -> None:
    """Publisher metadata must reach merger candidates for cross-publisher regroup."""

    entry = {
        "knowledge_object_type": "parameter_spec",
        "confidence_score": 0.9,
        "compile_metadata": {},
        "health_findings": [],
    }
    curation = {
        "title": "Oil temperature control",
        "summary": "Oil temperature control summary.",
        "structured_payload": {"parameter_name": "Oil temperature control"},
        "applicability": {},
        "trust_level": "L2",
        "publisher": "Gree",
        "citation": "Gree C-series manual p.66",
    }

    result = _base_manual_entry(
        entry,
        curation,
        {"chunk": {"chunk_id": "chunk_1"}},
        knowledge_object_id="ko_1",
        canonical_key="oil_temperature_control",
    )

    assert result["publisher"] == "Gree"
    assert result["citation"] == "Gree C-series manual p.66"
