"""Tests for model-reviewed standard pack drafting."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.apply_model_review_to_standard_packs import apply_model_review_to_pack_dir


def _write_pack(pack_dir: Path) -> Path:
    payload = {
        "review_mode": "chunk_backfill_review_pack",
        "domain_id": "hvac",
        "doc_id": "doc_g36",
        "doc_name": "ASHRAE G36.pdf",
        "equipment_class": {"equipment_class_id": "ahu", "equipment_class_key": "hvac:ahu", "label": "AHU"},
        "candidate_entries": [
            _entry("operational_sequence", "seq_key"),
            _entry("commissioning_procedure", "commissioning_key"),
        ],
    }
    path = pack_dir / "hvac__doc_g36__ahu.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _entry(ko_type: str, key: str) -> dict:
    return {
        "candidate_id": f"cand_{key}",
        "domain_id": "hvac",
        "doc_id": "doc_g36",
        "doc_name": "ASHRAE G36.pdf",
        "knowledge_object_type": ko_type,
        "canonical_key_candidate": key,
        "structured_payload_candidate": {"title": key, "summary": f"Summary {key}"},
        "evidence_text": "Verbatim evidence.",
        "chunk_id": "chunk_1",
        "source_chunk_ids": ["chunk_1"],
        "trust_level": "L3",
        "judge_verdict": "accepted",
        "judge_reason": "Useful standard knowledge.",
        "review_decision": "pending",
        "curation": {},
    }


def test_apply_model_review_accepts_supported_and_rejects_unsupported_types() -> None:
    """Model review drafts should be ready only for currently supported KO types."""

    with tempfile.TemporaryDirectory() as tmp_dir:
        pack_dir = Path(tmp_dir)
        pack_path = _write_pack(pack_dir)

        report = apply_model_review_to_pack_dir(pack_dir)
        pack = json.loads(pack_path.read_text(encoding="utf-8"))

    assert report["summary"] == {"accepted": 1, "rejected": 1}
    assert pack["candidate_entries"][0]["review_decision"] == "accepted"
    assert pack["candidate_entries"][0]["curation"]["review_source"] == "llm_judge"
    assert pack["candidate_entries"][1]["review_decision"] == "rejected"
    assert "unsupported_ko_type" in pack["candidate_entries"][1]["review_notes"]


def test_apply_model_review_rejected_source_matches_candidate_id_not_key() -> None:
    """Duplicate canonical keys can have one accepted and one rejected candidate."""

    with tempfile.TemporaryDirectory() as tmp_dir:
        pack_dir = Path(tmp_dir)
        pack_path = _write_pack(pack_dir)
        rejected_path = pack_dir / "judge_rejected.jsonl"
        rejected_path.write_text(
            json.dumps(
                {
                    "candidate_id": "different_candidate",
                    "canonical_key_candidate": "seq_key",
                    "judge_reason": "Duplicate unsupported extraction.",
                    "judge_category": "duplicate",
                }
            )
            + "\n",
            encoding="utf-8",
        )

        apply_model_review_to_pack_dir(pack_dir, rejected_path=rejected_path)
        pack = json.loads(pack_path.read_text(encoding="utf-8"))

    assert pack["candidate_entries"][0]["review_decision"] == "accepted"
