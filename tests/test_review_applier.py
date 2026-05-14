"""Tests for merger-aware review applier conversion."""

from packages.review.applier import candidate_to_merger_dict


def test_candidate_to_merger_dict_preserves_top_level_traceability_as_evidence() -> None:
    """Manual fixture entries carry primary traceability fields at the top level."""

    converted = candidate_to_merger_dict({
        "title": "Reviewed AUX E22",
        "summary": "Reviewed from stats flow.",
        "structured_payload": {"fault_code": "E22"},
        "confidence_score": 0.99,
        "trust_level": "L2",
        "chunk_id": "chunk_aux_module_faults_e22",
        "doc_id": "doc_aux_module_faults",
        "page_id": "page_aux_module_faults_4",
        "page_no": 4,
        "evidence_text": "High pressure switch protection.",
        "evidence_role": "primary",
    })

    assert converted["evidence"] == [
        {
            "chunk_id": "chunk_aux_module_faults_e22",
            "doc_id": "doc_aux_module_faults",
            "page_id": "page_aux_module_faults_4",
            "page_no": 4,
            "evidence_text": "High pressure switch protection.",
            "evidence_role": "primary",
        }
    ]


def test_candidate_to_merger_dict_preserves_nested_fixture_traceability_as_evidence() -> None:
    """Review-pack manual fixtures nest doc/page/chunk/evidence chain refs."""

    converted = candidate_to_merger_dict({
        "title": "Reviewed AUX E22",
        "summary": "Reviewed from stats flow.",
        "structured_payload": {"fault_code": "E22"},
        "chunk": {"chunk_id": "chunk_aux_module_faults_e22"},
        "doc": {"doc_id": "doc_aux_module_faults"},
        "page": {"page_id": "page_aux_module_faults_4", "page_no": 4},
        "evidence": {
            "evidence_text": "High pressure switch protection.",
            "evidence_role": "primary",
        },
    })

    assert converted["evidence"][0]["chunk_id"] == "chunk_aux_module_faults_e22"
    assert converted["evidence"][0]["doc_id"] == "doc_aux_module_faults"
    assert converted["evidence"][0]["page_id"] == "page_aux_module_faults_4"
    assert converted["evidence"][0]["page_no"] == 4
    assert converted["evidence"][0]["evidence_text"] == "High pressure switch protection."
