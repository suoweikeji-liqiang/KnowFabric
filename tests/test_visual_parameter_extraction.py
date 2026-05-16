"""Tests for scanned-page visual parameter extraction normalization."""

from __future__ import annotations

from packages.extraction.visual_parameter_extraction import (
    build_visual_parameter_messages,
    normalize_visual_candidates,
)


def test_normalize_visual_candidates_keeps_reviewable_parameter() -> None:
    payload = {
        "candidates": [
            {
                "knowledge_object_type": "parameter_spec",
                "parameter_name": "油压差范围",
                "range_min": "150",
                "range_max": "250",
                "unit": "kPa",
                "evidence_quote": "油压差范围 150~250 kPa",
                "confidence": 0.92,
            }
        ]
    }

    candidates = normalize_visual_candidates(payload, page_no=12)

    assert len(candidates) == 1
    assert candidates[0].structured_payload["parameter_name"] == "油压差范围"
    assert candidates[0].structured_payload["unit"] == "kPa"
    assert candidates[0].page_no == 12


def test_normalize_visual_candidates_filters_junk_names_and_empty_evidence() -> None:
    payload = {
        "candidates": [
            {"knowledge_object_type": "parameter_spec", "parameter_name": "EN", "evidence_quote": "EN"},
            {"knowledge_object_type": "parameter_spec", "parameter_name": "油温", "evidence_quote": ""},
        ]
    }

    assert normalize_visual_candidates(payload, page_no=1) == []


def test_visual_parameter_prompt_includes_image_and_schema() -> None:
    messages = build_visual_parameter_messages(
        image_url="data:image/png;base64,abc",
        page_no=3,
        equipment_class_id="centrifugal_chiller",
    )

    assert messages[0]["role"] == "system"
    assert "parameter_spec" in messages[0]["content"]
    assert "fault_code" in messages[0]["content"]
    assert messages[1]["content"][1]["image_url"]["url"] == "data:image/png;base64,abc"
