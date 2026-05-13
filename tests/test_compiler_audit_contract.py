"""Tests for compiler run/source manifest/audit packet contracts."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.audit import (
    build_compiler_audit_packet,
    build_compiler_run,
    build_review_pack_source_manifest_entry,
)


def test_review_pack_source_manifest_records_hash_and_doc_ids(tmp_path: Path) -> None:
    pack_path = tmp_path / "hvac__doc_a__chiller.json"
    payload = {
        "review_mode": "chunk_backfill_review_pack",
        "domain_id": "hvac",
        "candidate_entries": [
            {"evidence": [{"doc_id": "doc_b"}, {"doc_id": "doc_a"}]},
            {"evidence": [{"doc_id": "doc_a"}]},
        ],
    }
    pack_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    entry = build_review_pack_source_manifest_entry(pack_path, payload)

    assert entry.source_id == "hvac__doc_a__chiller"
    assert entry.source_type == "review_pack"
    assert entry.domain_id == "hvac"
    assert entry.doc_ids == ["doc_a", "doc_b"]
    assert len(entry.content_sha256) == 64
    assert entry.path.endswith("hvac__doc_a__chiller.json")


def test_compiler_audit_packet_preserves_run_inputs_and_failure_flags(tmp_path: Path) -> None:
    pack_path = tmp_path / "pack.json"
    payload = {
        "review_mode": "chunk_backfill_review_pack",
        "domain_id": "hvac",
        "candidate_entries": [{"evidence": [{"doc_id": "doc_a"}]}],
    }
    pack_path.write_text(json.dumps(payload), encoding="utf-8")
    source = build_review_pack_source_manifest_entry(pack_path, payload)
    run = build_compiler_run(
        compiler_run_id="run_fixed",
        pipeline="review_pack_batch_apply",
        domain_id="hvac",
        source_manifest=[source],
        parameters={"use_merger": True},
    )

    packet = build_compiler_audit_packet(
        compiler_run=run,
        summary={"applied": 0, "failed": 1},
        results=[{"pack_file": "pack.json", "status": "failed", "error": "merger unavailable"}],
    )

    assert packet.compiler_run.compiler_run_id == "run_fixed"
    assert packet.source_manifest[0].doc_ids == ["doc_a"]
    assert packet.integrity_checks["source_manifest_count"] == 1
    assert packet.integrity_checks["failed_result_count"] == 1
    assert "has_failed_results" in packet.audit_flags
