"""Tests for the official standard import pipeline orchestrator."""

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.run_standard_import_pipeline import (
    materialize_candidate_file_from_run,
    run_standard_import_pipeline,
)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def _candidate(candidate_id: str = "cand_1") -> dict:
    return {
        "candidate_id": candidate_id,
        "domain_id": "hvac",
        "doc_id": "doc_standard",
        "doc_name": "ASHRAE standard.pdf",
        "knowledge_object_type": "operational_sequence",
        "canonical_key_candidate": f"ashrae:g36:operational_sequence:{candidate_id}",
        "structured_payload_candidate": {"knowledge_type": "operational_sequence", "title": "Sequence"},
        "evidence_text": "Verbatim evidence.",
        "equipment_class_candidate": {
            "equipment_class_id": "chiller",
            "equipment_class_key": "hvac:chiller",
            "label": "Chiller",
            "supported_knowledge_anchors": ["operational_sequence"],
        },
    }


def _args(tmp_dir: str, **overrides) -> argparse.Namespace:
    values = {
        "standard": "ashrae-g36",
        "workspace_dir": tmp_dir,
        "from_run_dir": None,
        "candidate_file": None,
        "review_pack_dir": None,
        "skip_review_pack_build": False,
        "skip_readiness": False,
        "apply": False,
        "smoke": False,
        "default_trust_level": "L3",
        "min_trust_level": "L3",
        "extract": False,
        "doc_id": None,
        "sections": "5.1.14,5.20,5.21",
        "extract_backend": None,
        "judge_backend": None,
        "extract_output_dir": "output/ashrae_guideline36_vertical",
        "budget_rmb": 30.0,
        "max_section_tokens": 250_000,
        "max_candidates_per_section": 24,
        "extract_mode": "section",
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def test_materialize_candidate_file_from_run_writes_candidate_entries() -> None:
    """Verified JSONL from an extraction run should become review-pack candidate JSON."""

    with tempfile.TemporaryDirectory() as tmp_dir:
        run_dir = Path(tmp_dir) / "run"
        workspace_dir = Path(tmp_dir) / "workspace"
        run_dir.mkdir()
        _write_jsonl(run_dir / "candidates_llm_verified.jsonl", [_candidate()])
        _write_json(
            run_dir / "summary.json",
            {
                "standard_id": "ASHRAE Guideline 36-2021",
                "doc_id": "doc_standard",
                "manual": "ASHRAE standard.pdf",
                "sections": ["5.20"],
                "judge_accepted": 1,
            },
        )

        payload = materialize_candidate_file_from_run(run_dir, workspace_dir)

        written = json.loads(Path(payload["candidate_path"]).read_text(encoding="utf-8"))
    assert written["metadata"]["total_candidates"] == 1
    assert written["metadata"]["standard_id"] == "ASHRAE Guideline 36-2021"
    assert written["candidate_entries"][0]["candidate_id"] == "cand_1"
    assert written["candidate_entries"][0]["equipment_class_candidate"]["equipment_class_id"] == "chiller"


def test_materialize_candidate_file_from_run_maps_ahu_sections_to_ahu() -> None:
    """G36 airside sections should not be defaulted to chiller."""

    with tempfile.TemporaryDirectory() as tmp_dir:
        run_dir = Path(tmp_dir) / "run"
        workspace_dir = Path(tmp_dir) / "workspace"
        run_dir.mkdir()
        candidate = _candidate()
        candidate["structured_payload_candidate"]["section_id"] = "5.16.1.1"
        candidate.pop("equipment_class_candidate")
        _write_jsonl(run_dir / "candidates_llm_verified.jsonl", [candidate])
        _write_json(run_dir / "summary.json", {"standard_id": "ASHRAE Guideline 36-2021"})

        payload = materialize_candidate_file_from_run(run_dir, workspace_dir)

        written = json.loads(Path(payload["candidate_path"]).read_text(encoding="utf-8"))
    assert written["candidate_entries"][0]["equipment_class_candidate"]["equipment_class_id"] == "ahu"


def test_materialize_candidate_file_from_run_maps_remaining_airside_sections_to_ahu() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        run_dir = Path(tmp_dir) / "run"
        workspace_dir = Path(tmp_dir) / "workspace"
        run_dir.mkdir()
        candidate = _candidate()
        candidate["structured_payload_candidate"]["section_id"] = "5.22.6.1"
        candidate.pop("equipment_class_candidate")
        _write_jsonl(run_dir / "candidates_llm_verified.jsonl", [candidate])
        _write_json(run_dir / "summary.json", {"standard_id": "ASHRAE Guideline 36-2021"})

        payload = materialize_candidate_file_from_run(run_dir, workspace_dir)

        written = json.loads(Path(payload["candidate_path"]).read_text(encoding="utf-8"))
    assert written["candidate_entries"][0]["equipment_class_candidate"]["equipment_class_id"] == "ahu"


def test_materialize_candidate_file_from_run_normalizes_commissioning_procedure() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        run_dir = Path(tmp_dir) / "run"
        workspace_dir = Path(tmp_dir) / "workspace"
        run_dir.mkdir()
        candidate = _candidate()
        candidate.pop("equipment_class_candidate")
        candidate["knowledge_object_type"] = "commissioning_procedure"
        candidate["canonical_key_candidate"] = "ashrae:g36:commissioning_procedure:5_16_15:testing"
        candidate["structured_payload_candidate"]["knowledge_type"] = "commissioning_procedure"
        candidate["structured_payload_candidate"]["section_id"] = "5.16.15"
        _write_jsonl(run_dir / "candidates_llm_verified.jsonl", [candidate])
        _write_json(run_dir / "summary.json", {"standard_id": "ASHRAE Guideline 36-2021"})

        payload = materialize_candidate_file_from_run(run_dir, workspace_dir)

        written = json.loads(Path(payload["candidate_path"]).read_text(encoding="utf-8"))
    entry = written["candidate_entries"][0]
    assert entry["knowledge_object_type"] == "commissioning_step"
    assert ":commissioning_step:" in entry["canonical_key_candidate"]
    assert entry["structured_payload_candidate"]["knowledge_type"] == "commissioning_step"


def test_run_standard_import_pipeline_builds_packs_and_reports_pending() -> None:
    """Pipeline should generate pending review packs and stop before apply by default."""

    with tempfile.TemporaryDirectory() as tmp_dir:
        run_dir = Path(tmp_dir) / "run"
        run_dir.mkdir()
        _write_jsonl(run_dir / "candidates_llm_verified.jsonl", [_candidate()])
        _write_json(run_dir / "summary.json", {"standard_id": "ASHRAE Guideline 36-2021", "doc_id": "doc_standard"})

        summary = run_standard_import_pipeline(_args(tmp_dir, from_run_dir=str(run_dir)))

        pack_path = Path(tmp_dir) / "review_packs" / "hvac__doc_standard__chiller.json"
        pack = json.loads(pack_path.read_text(encoding="utf-8"))

    assert summary["candidate_count"] == 1
    assert summary["review_pack_count"] == 1
    assert summary["readiness_summary"]["blocked_pending"] == 1
    assert "Complete review decisions" in summary["next_action"]
    assert pack["candidate_entries"][0]["review_decision"] == "pending"


def test_run_standard_import_pipeline_can_use_reviewed_pack_dir(monkeypatch) -> None:
    """Existing reviewed packs should be passable straight to backfill/smoke orchestration."""

    monkeypatch.setattr(
        "scripts.run_standard_import_pipeline.run_standard_review_backfill",
        lambda **kwargs: {
            "readiness_summary": {"ready": 1, "blocked_pending": 0},
            "apply_summary": {"applied": 1, "failed": 0},
            "api_smoke_summary": {"targets": 1, "passed": 1, "failed": 0},
        },
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        pack_dir = Path(tmp_dir) / "reviewed_packs"
        pack_dir.mkdir()
        summary = run_standard_import_pipeline(
            _args(
                tmp_dir,
                review_pack_dir=str(pack_dir),
                skip_review_pack_build=True,
                apply=True,
                smoke=True,
            )
        )

    assert summary["review_pack_dir"] == str(pack_dir)
    assert summary["apply_summary"]["applied"] == 1
    assert summary["api_smoke_summary"]["passed"] == 1
    assert "ready for consumer validation" in summary["next_action"]
