"""Tests for cross-source knowledge object merger."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.cross_source_merger import (
    _available_matched_ids,
    _build_contextual_name,
    _coerce_numeric,
    _compute_consensus_state,
    _enrich_layer_range_from_prose,
    _extract_prose_range,
    _extract_value_summary,
    _values_agree,
    merge_candidates,
)


def test_extract_prose_range_chinese_unit_inline() -> None:
    """F9: Chinese prose with unit inline (20℃～34℃) yields (20, 34)."""
    assert _extract_prose_range("冷却水进水温度应在 20℃～34℃ 之间。") == ("20", "34")
    assert _extract_prose_range("油温在 -5℃~10℃") == ("-5", "10")
    assert _extract_prose_range("范围 20℃到34℃") == ("20", "34")


def test_extract_prose_range_english_unit() -> None:
    """F9: English prose with °C/°F."""
    assert _extract_prose_range("Range: 20°C to 34°C") == ("20", "34")
    assert _extract_prose_range("between 20 and 34") == ("20", "34")


def test_extract_prose_range_ambiguous_returns_none() -> None:
    """F9: when multiple distinct ranges in prose, return None (don't guess)."""
    assert _extract_prose_range("油温 20℃-34℃；水温 30℃-50℃") is None
    assert _extract_prose_range("") is None
    assert _extract_prose_range(None) is None


def test_enrich_layer_range_populates_from_evidence() -> None:
    """F9: layer without range_min/max gets populated from evidence_text prose."""
    layer = {"structured_payload": {"parameter_name": "冷却水温度"}}
    evidence = [{"evidence_text": "冷却水进水温度应在 20℃～34℃ 之间。"}]
    _enrich_layer_range_from_prose(layer, evidence)
    assert layer["structured_payload"]["range_min"] == "20"
    assert layer["structured_payload"]["range_max"] == "34"
    assert layer["structured_payload"]["range_source"] == "prose_extracted"


def test_enrich_layer_range_skips_when_already_populated() -> None:
    """F9: do not overwrite existing range_min/max (those are authoritative)."""
    layer = {"structured_payload": {"range_min": "10", "range_max": "20"}}
    evidence = [{"evidence_text": "20℃～34℃ 范围"}]
    _enrich_layer_range_from_prose(layer, evidence)
    assert layer["structured_payload"]["range_min"] == "10"
    assert layer["structured_payload"]["range_max"] == "20"
    assert "range_source" not in layer["structured_payload"]


def test_enrich_layer_range_noop_when_no_match() -> None:
    """F9: when evidence prose has no parseable range, leave layer unchanged."""
    layer = {"structured_payload": {"parameter_name": "fault_name"}}
    evidence = [{"evidence_text": "压缩机停机：油压差报警。"}]
    _enrich_layer_range_from_prose(layer, evidence)
    assert "range_min" not in layer["structured_payload"]
    assert "range_max" not in layer["structured_payload"]


def test_extract_value_summary_no_unit_duplication() -> None:
    """F6: when value already ends with unit, do not duplicate."""

    # Common pattern from real corpus: value contains range with unit suffix
    cand = {"structured_payload": {"value": "20～34℃", "unit": "℃"}}
    assert _extract_value_summary(cand) == "20～34℃", "must not become 20～34℃℃"

    # Same for SEC, % and other unit strings
    cand = {"structured_payload": {"value": "40SEC", "unit": "SEC"}}
    assert _extract_value_summary(cand) == "40SEC", "must not become 40SECSEC"

    cand = {"structured_payload": {"value": "5%", "unit": "%"}}
    assert _extract_value_summary(cand) == "5%", "must not become 5%%"

    # Normal case: value is bare number, unit appended correctly
    cand = {"structured_payload": {"value": "15", "unit": "kPa"}}
    assert _extract_value_summary(cand) == "15kPa"

    # No unit at all
    cand = {"structured_payload": {"value": "44"}}
    assert _extract_value_summary(cand) == "44"

    # Range fallback when no value
    cand = {"structured_payload": {"range_min": "10", "range_max": "20"}}
    assert _extract_value_summary(cand) == "[10, 20]"

    # None payload → fall through to title
    cand = {"title": "Some title", "structured_payload": {}}
    assert _extract_value_summary(cand) == "Some title"


def _make_candidate(
    title: str,
    value: str | None = None,
    default_value: str | None = None,
    authority_level: str = "oem_manual",
    publisher: str = "Trane",
    citation: str = "Trane Manual p.29",
    doc_id: str = "doc_001",
    chunk_id: str = "chunk_001",
    confidence: float = 0.9,
    trust_level: str = "L4",
    evidence_text: str = "Test evidence text",
) -> dict:
    return {
        "title": title,
        "summary": f"Summary for {title}",
        "structured_payload": {
            "value": value,
            "default_value": default_value,
        },
        "confidence_score": confidence,
        "trust_level": trust_level,
        "review_status": "published",
        "authority_level": authority_level,
        "publisher": publisher,
        "citation": citation,
        "doc_id": doc_id,
        "evidence": [
            {
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "page_id": "page_001",
                "page_no": 29,
                "evidence_text": evidence_text,
                "evidence_role": "primary",
            }
        ],
    }


def test_single_candidate_returns_single_source():
    candidates = [
        _make_candidate("CHWS Setpoint", value="44F", default_value="44F"),
    ]
    result = merge_candidates(
        candidates,
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        ontology_class_key="hvac:centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )
    assert len(result) == 1
    assert result[0]["consensus_state"] == "single_source"
    assert result[0]["highest_authority_level"] == "oem_manual"
    assert result[0]["conflict_summary"] is None
    assert len(result[0]["authority_summary_json"]["layers"]) == 1


def test_two_candidates_same_value_returns_agreed():
    candidates = [
        _make_candidate("CHWS Setpoint", value="44F", doc_id="doc_trane", chunk_id="chunk_trane",
                         authority_level="oem_manual", publisher="Trane",
                         citation="Trane Manual p.29"),
        _make_candidate("CHWS Setpoint", value="44F", doc_id="doc_york", chunk_id="chunk_york",
                         authority_level="oem_manual", publisher="York",
                         citation="York YK Manual p.43"),
    ]
    result = merge_candidates(
        candidates,
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        ontology_class_key="hvac:centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )
    assert len(result) == 1
    assert result[0]["consensus_state"] == "agreed"
    assert len(result[0]["authority_summary_json"]["layers"]) == 2
    assert len(result[0]["evidence_rows"]) == 2


def test_different_values_produces_conflict():
    candidates = [
        _make_candidate("CHWS Setpoint", value="44F", doc_id="doc_trane", chunk_id="chunk_trane",
                         authority_level="oem_manual", publisher="Trane"),
        _make_candidate("CHWS Setpoint", value="50F", doc_id="doc_york", chunk_id="chunk_york",
                         authority_level="oem_manual", publisher="York"),
    ]
    result = merge_candidates(
        candidates,
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        ontology_class_key="hvac:centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )
    assert len(result) == 1
    assert result[0]["consensus_state"] == "material_conflict"
    assert result[0]["conflict_summary"] is not None


def test_similar_numeric_values_within_tolerance():
    candidates = [
        _make_candidate("Setpoint", value="44.0", doc_id="doc_a", chunk_id="chunk_a"),
        _make_candidate("Setpoint", value="44.2", doc_id="doc_b", chunk_id="chunk_b"),
    ]
    result = merge_candidates(
        candidates,
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        ontology_class_key="hvac:centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )
    assert result[0]["consensus_state"] == "agreed"


def test_numeric_values_outside_tolerance():
    candidates = [
        _make_candidate("Setpoint", value="44.0", doc_id="doc_a", chunk_id="chunk_a"),
        _make_candidate("Setpoint", value="50.0", doc_id="doc_b", chunk_id="chunk_b"),
    ]
    result = merge_candidates(
        candidates,
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        ontology_class_key="hvac:centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )
    assert result[0]["consensus_state"] == "material_conflict"


def test_authority_rank_assignment():
    candidates = [
        _make_candidate("Setpoint", value="44F", doc_id="doc_ashrae", chunk_id="chunk_a",
                         authority_level="industry_standard", publisher="ASHRAE",
                         citation="ASHRAE 90.1-2022 §6.5.3.2"),
        _make_candidate("Setpoint", value="44F", doc_id="doc_trane", chunk_id="chunk_b",
                         authority_level="oem_manual", publisher="Trane"),
    ]
    result = merge_candidates(
        candidates,
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        ontology_class_key="hvac:centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )
    assert result[0]["highest_authority_level"] == "industry_standard"
    assert result[0]["consensus_state"] == "agreed"


def test_material_conflict_includes_authority_arbitration_result():
    candidates = [
        _make_candidate("CHWS Setpoint", value="44F", doc_id="doc_ashrae", chunk_id="chunk_ashrae",
                         authority_level="industry_standard", publisher="ASHRAE",
                         citation="ASHRAE G36 §5.22"),
        _make_candidate("CHWS Setpoint", value="50F", doc_id="doc_trane", chunk_id="chunk_trane",
                         authority_level="oem_manual", publisher="Trane",
                         citation="Trane Manual p.29"),
    ]

    result = merge_candidates(
        candidates,
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        ontology_class_key="hvac:centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )

    arbitration = result[0]["deviation_justification_json"]["authority_arbitration"]
    assert result[0]["consensus_state"] == "material_conflict"
    assert arbitration["recommended_value"] == "44F"
    assert arbitration["recommended_authority_level"] == "industry_standard"
    assert arbitration["arbitration_rule_applied"] == "rule_3_standard_over_oem"


def test_value_agree_helpers():
    assert _values_agree("44F", "44F") is True
    assert _values_agree("44.0F", "44F") is True   # numeric: both 44.0
    assert _values_agree(44.0, 44.2) is True      # within 5%
    assert _values_agree(44.0, 48.0) is False     # outside 5%
    assert _values_agree(None, None) is True
    assert _values_agree("44F", None) is True   # R3: empty value treated as agree (no data to compare)

def test_temperature_unit_conversion():
    """R4: °F ↔ °C unit normalization."""
    assert _values_agree("95°F", "35°C") is True    # 95F = 35C, exact
    assert _values_agree("95°F", "32°C") is True    # 95F = 35C, diff from 32C is 8.6% within 10%
    assert _values_agree("100°F", "50°C") is False  # 100F = 37.8C, diff from 50C is 24% outside 10%
    assert _values_agree("32°F", "0°C") is True     # 32F = 0C, exact

def test_pressure_unit_conversion():
    """R4: pressure unit normalization."""
    assert _values_agree("120psi", "8.27bar") is True   # 120 psi ≈ 8.27 bar
    assert _values_agree("1MPa", "10bar") is True       # 1 MPa = 10 bar
    assert _values_agree("100kPa", "1bar") is True      # 100 kPa = 1 bar
    assert _values_agree("100psi", "10bar") is False    # 100 psi ≈ 6.89 bar, diff is 31%

def test_empty_value_short_circuit():
    """R3: empty/missing values treated as agree."""
    assert _values_agree("", "") is True
    assert _values_agree("44F", "") is True
    assert _values_agree(None, "some value") is True
    assert _values_agree("none", "N/A") is True


def test_keyword_facet_detection_removed_from_consensus():
    """String keyword facets are not used to override value disagreement."""
    from packages.compiler.cross_source_merger import _compute_consensus_state
    layers = [
        {"value_summary": "Setpoint: 44F", "citation": "Trane CVGF p.29"},
        {"value_summary": "Limit: 38F (cutout)", "citation": "Carrier 19XR p.37"},
    ]
    state, summary = _compute_consensus_state(layers)
    assert state == "material_conflict"
    assert "disagree" in (summary or "").lower()


def test_merger_sanity_pathological_split(monkeypatch):
    """E3: defensive sanity forces split of oversized groups (LLM path only)."""
    monkeypatch.setenv("KNOWFABRIC_USE_EMBEDDING_FIRST", "0")
    import importlib, packages.compiler.cross_source_merger as ckmod
    importlib.reload(ckmod)
    from packages.compiler.cross_source_merger import MERGER_MAX_GROUP_CANDIDATES
    from unittest.mock import patch

    candidates = []
    for i in range(MERGER_MAX_GROUP_CANDIDATES + 2):  # 7 candidates
        candidates.append({
            "title": f"unrelated_param_{i}",
            "structured_payload": {"parameter_name": f"unrelated_param_{i}"},
            "confidence_score": 0.85, "trust_level": "L3",
            "authority_level": "oem_manual", "publisher": "Test",
            "evidence": [{"chunk_id": "c1", "doc_id": "d1", "page_no": 1,
                "evidence_text": "test", "evidence_role": "primary"}],
        })

    # Mock group_and_normalize to return all-in-one bad key
    bad_key = "bad_merge_key"
    name_map = {c["title"]: bad_key for c in candidates}
    with patch.object(ckmod, "group_and_normalize", return_value=name_map):
        merged_result = ckmod.merge_candidates(
            candidates, domain_id="hvac",
            equipment_class_id="centrifugal_chiller",
            ontology_class_key="hvac:centrifugal_chiller",
            knowledge_object_type="parameter_spec",
        )

    # Sanity check should split them into multiple KOs
    unique_keys = {ko["canonical_key"] for ko in merged_result}
    assert len(unique_keys) >= MERGER_MAX_GROUP_CANDIDATES, \
        f"Expected >={MERGER_MAX_GROUP_CANDIDATES} unique keys after split, got {len(unique_keys)}"
    assert _values_agree(0, 0) is True


def test_merge_candidates_splits_distinct_same_document_parameter_names(monkeypatch):
    """A single manual's distinct parameters must not disappear into one KO."""

    from packages.compiler.cross_source_merger import merge_candidates

    names = [
        "供油温度范围",
        "油压差范围（运行）",
        "油压差范围（启动）",
        "油箱温度控制",
    ]
    monkeypatch.setattr(
        "packages.compiler.cross_source_merger.group_and_normalize",
        lambda names, **_kwargs: {
            name: "hvac:centrifugal_chiller:parameter:overmerged_oil_group"
            for name in names
        },
    )
    candidates = [
        {
            "title": name,
            "summary": name,
            "structured_payload": {"parameter_name": name},
            "confidence_score": 0.95,
            "trust_level": "L3",
            "publisher": "Gree",
            "citation": "Gree p.66",
            "authority_level": "oem_manual",
            "evidence": [{
                "chunk_id": f"chunk_{idx}",
                "doc_id": "doc_gree",
                "page_id": "page_66",
                "page_no": 66,
                "evidence_text": name,
                "evidence_role": "primary",
            }],
        }
        for idx, name in enumerate(names)
    ]

    merged = merge_candidates(
        candidates,
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        ontology_class_key="hvac:centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )

    merged_names = {
        ko["structured_payload_json"]["parameter_name"]
        for ko in merged
    }
    assert merged_names == set(names)
    assert all(len(ko["authority_summary_json"]["layers"]) == 1 for ko in merged)


def test_merge_candidates_caps_embedding_path_group_layers(monkeypatch):
    """Final merger grouping must not emit a KO with more than 8 layers."""

    from packages.compiler.cross_source_merger import merge_candidates

    candidates = []
    for idx in range(9):
        title = f"Distinct Param {idx}"
        candidate = _make_candidate(
            title,
            value=str(idx),
            publisher="Carrier" if idx % 2 else "York",
            doc_id=f"doc_{idx}",
            chunk_id=f"chunk_{idx}",
        )
        candidate["structured_payload"]["parameter_name"] = title
        candidates.append(candidate)

    monkeypatch.setattr(
        "packages.compiler.cross_source_merger.group_and_normalize",
        lambda names, **_kwargs: {
            name: "hvac:centrifugal_chiller:parameter:oversize_group"
            for name in names
        },
    )

    merged = merge_candidates(
        candidates,
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        ontology_class_key="hvac:centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )

    assert max(len(ko["authority_summary_json"]["layers"]) for ko in merged) <= 8


def test_build_contextual_name_includes_summary_and_value_fields():
    payload = {
        "parameter_name": "供油温度范围",
        "summary": "用于润滑油供油温度控制的范围。" * 10,
        "range_min": "35",
        "range_max": "50",
        "unit": "℃",
    }

    contextual = _build_contextual_name(payload)

    assert contextual.startswith("供油温度范围。")
    assert "用于润滑油供油温度控制的范围" in contextual
    assert "range_min=35" in contextual
    assert "range_max=50" in contextual
    assert "unit=℃" in contextual
    assert len(contextual.split("。")[1]) <= 120


def test_merge_candidates_uses_contextual_names_without_changing_facet_source(monkeypatch):
    captured = {}
    facet_calls = []

    def fake_group_and_normalize(names, **kwargs):
        captured["names"] = list(names)
        captured["facet_hints"] = dict(kwargs["facet_hints"])
        return {name: f"hvac:centrifugal_chiller:parameter:key_{idx}" for idx, name in enumerate(names)}

    def fake_detect_facet(name, payload):
        facet_calls.append((name, payload))
        return "temperature", "oil_temperature"

    monkeypatch.setattr(
        "packages.compiler.cross_source_merger.group_and_normalize",
        fake_group_and_normalize,
    )
    monkeypatch.setattr(
        "packages.compiler.cross_source_merger.detect_facet_v2",
        fake_detect_facet,
    )

    candidate = _make_candidate("fallback title", value=None)
    candidate["summary"] = "candidate summary should be available to embedding"
    candidate["structured_payload"] = {
        "parameter_name": "供油温度范围",
        "range_min": "35",
        "range_max": "50",
        "unit": "℃",
    }

    merge_candidates(
        [candidate],
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        ontology_class_key="hvac:centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )

    assert captured["names"] == [
        "供油温度范围。candidate summary should be available to embedding。"
        "range_min=35 range_max=50 unit=℃"
    ]
    assert facet_calls == [
        (
            "供油温度范围",
            {
                "parameter_name": "供油温度范围",
                "range_min": "35",
                "range_max": "50",
                "unit": "℃",
                "title": "fallback title",
                "summary": "candidate summary should be available to embedding",
                "value_summary": "[35, 50]",
            },
        )
    ]
    assert captured["facet_hints"] == {
        captured["names"][0]: ("temperature", "oil_temperature")
    }


def test_contextual_embedding_does_not_make_value_based_canonical_key(monkeypatch):
    def fake_group_and_normalize(names, **_kwargs):
        return {
            name: "hvac:centrifugal_chiller:parameter:35_50"
            for name in names
        }

    monkeypatch.setattr(
        "packages.compiler.cross_source_merger.group_and_normalize",
        fake_group_and_normalize,
    )
    candidate = _make_candidate("供油温度范围", value=None)
    candidate["structured_payload"] = {
        "parameter_name": "供油温度范围",
        "range_min": "35",
        "range_max": "50",
        "unit": "℃",
    }

    merged = merge_candidates(
        [candidate],
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        ontology_class_key="hvac:centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )

    assert merged[0]["canonical_key"].endswith(":supply_oil_temperature_range")


def test_upsert_matching_does_not_reuse_existing_ko_id_across_split_groups():
    """One old KO split into two output groups must not be overwritten twice."""

    first_group = _available_matched_ids(
        {"ko_existing"},
        removed_ko_ids=set(),
        assigned_ko_ids=set(),
    )
    second_group = _available_matched_ids(
        {"ko_existing"},
        removed_ko_ids=set(),
        assigned_ko_ids=first_group,
    )

    assert first_group == {"ko_existing"}
    assert second_group == set()


def test_consensus_state_scoring():
    layers_single = [{"value_summary": "44F"}]
    state, summary = _compute_consensus_state(layers_single)
    assert state == "single_source"
    assert summary is None

    layers_agreed = [{"value_summary": "44F"}, {"value_summary": "44F"}]
    state, summary = _compute_consensus_state(layers_agreed)
    assert state == "agreed"

    layers_conflict = [{"value_summary": "44F"}, {"value_summary": "50F"}]
    state, summary = _compute_consensus_state(layers_conflict)
    assert state == "material_conflict"


if __name__ == "__main__":
    test_single_candidate_returns_single_source()
    test_two_candidates_same_value_returns_agreed()
    test_different_values_produces_conflict()
    test_similar_numeric_values_within_tolerance()
    test_numeric_values_outside_tolerance()
    test_authority_rank_assignment()
    test_value_agree_helpers()
    test_consensus_state_scoring()
    print("Cross-source merger tests passed")
