"""Tests for the standard review backfill orchestrator."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.run_standard_review_backfill import (
    _accepted_smoke_targets,
    run_semantic_smoke,
    run_standard_review_backfill,
)


def _write_pack(
    pack_dir: Path,
    name: str,
    *,
    equipment_class_id: str,
    entries: list[dict],
) -> Path:
    payload = {
        "review_mode": "chunk_backfill_review_pack",
        "domain_id": "hvac",
        "doc_id": "doc_standard",
        "doc_name": "ASHRAE standard.pdf",
        "equipment_class": {
            "equipment_class_id": equipment_class_id,
            "equipment_class_key": f"hvac:{equipment_class_id}",
        },
        "candidate_entries": entries,
    }
    path = pack_dir / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _entry(ko_type: str, decision: str = "accepted") -> dict:
    return {
        "candidate_id": f"cand_{ko_type}_{decision}",
        "knowledge_object_type": ko_type,
        "review_decision": decision,
    }


def test_accepted_smoke_targets_ignore_non_pack_json_and_group_counts() -> None:
    """Smoke target discovery should use only accepted entries in real packs."""

    with tempfile.TemporaryDirectory() as tmp_dir:
        pack_dir = Path(tmp_dir)
        _write_pack(
            pack_dir,
            "hvac__doc_standard__chiller.json",
            equipment_class_id="chiller",
            entries=[_entry("operational_sequence"), _entry("operational_sequence"), _entry("parameter_spec", "rejected")],
        )
        _write_pack(
            pack_dir,
            "hvac__doc_standard__hot_water_plant.json",
            equipment_class_id="hot_water_plant",
            entries=[_entry("operational_sequence")],
        )
        (pack_dir / "api_smoke_report.json").write_text(json.dumps({"report_mode": "old"}), encoding="utf-8")

        targets = _accepted_smoke_targets(pack_dir)

    assert targets == [
        {
            "domain_id": "hvac",
            "equipment_class_id": "chiller",
            "knowledge_object_type": "operational_sequence",
            "service_family": "operational_guidance",
            "expected_accepted_count": 2,
        },
        {
            "domain_id": "hvac",
            "equipment_class_id": "hot_water_plant",
            "knowledge_object_type": "operational_sequence",
            "service_family": "operational_guidance",
            "expected_accepted_count": 1,
        },
    ]


def test_run_semantic_smoke_reports_visible_counts(monkeypatch) -> None:
    """Semantic smoke should compare accepted pack counts to service-visible KOs."""

    class FakeDb:
        def close(self) -> None:
            self.closed = True

    class FakeService:
        def get_operational_guidance(self, **kwargs):
            count = 2 if kwargs["equipment_class_id"] == "chiller" else 0
            return {
                "items": [{"knowledge_object_type": "operational_sequence"} for _ in range(count)],
                "total_count": count,
                "returned_count": count,
                "has_more": False,
            }

    monkeypatch.setattr("scripts.run_standard_review_backfill.SessionLocal", FakeDb)
    monkeypatch.setattr("scripts.run_standard_review_backfill.SemanticRetrievalService", FakeService)

    with tempfile.TemporaryDirectory() as tmp_dir:
        pack_dir = Path(tmp_dir)
        _write_pack(
            pack_dir,
            "hvac__doc_standard__chiller.json",
            equipment_class_id="chiller",
            entries=[_entry("operational_sequence"), _entry("operational_sequence")],
        )
        _write_pack(
            pack_dir,
            "hvac__doc_standard__hot_water_plant.json",
            equipment_class_id="hot_water_plant",
            entries=[_entry("operational_sequence")],
        )

        report = run_semantic_smoke(pack_dir)
        assert Path(report["report_path"]).exists()

    assert report["summary"] == {"targets": 2, "passed": 1, "failed": 1}
    assert report["results"][0]["status"] == "pass"
    assert report["results"][1]["status"] == "fail"


def test_run_standard_review_backfill_writes_summary_outputs(monkeypatch) -> None:
    """The orchestrator should run selected stages and persist JSON/Markdown summaries."""

    monkeypatch.setattr(
        "scripts.run_standard_review_backfill.check_review_pack_directory",
        lambda pack_dir: {"summary": {"ready": 1}, "report_path": str(Path(pack_dir) / "ready.json")},
    )
    monkeypatch.setattr(
        "scripts.run_standard_review_backfill.apply_review_packs_in_directory",
        lambda pack_dir, fixtures_output_dir=None: {
            "summary": {"applied": 1, "skipped_pending": 0, "skipped_no_accepted": 0, "failed": 0},
            "report_path": str(Path(pack_dir) / "apply.json"),
        },
    )
    monkeypatch.setattr(
        "scripts.run_standard_review_backfill.run_semantic_smoke",
        lambda pack_dir, min_trust_level="L3": {
            "summary": {"targets": 1, "passed": 1, "failed": 0},
            "report_path": str(Path(pack_dir) / "api_smoke_report.json"),
        },
    )
    monkeypatch.setattr(
        "scripts.run_standard_review_backfill.summarize_review_pipeline_stats",
        lambda **kwargs: {"overall": {}, "documents": [], "review_packs": []},
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        summary = run_standard_review_backfill(review_pack_dir=tmp_dir, apply=True, smoke=True)
        assert Path(summary["summary_path"]).exists()
        assert Path(summary["markdown_path"]).exists()

    assert summary["apply_summary"]["applied"] == 1
    assert summary["api_smoke_summary"]["passed"] == 1
