"""Tests for document-level HVAC extraction batch helpers."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.llm_compiler import OpenAICompatibleBackend
from packages.db.models import ContentChunk, Document, DocumentPage
from scripts.llm_backend_config import resolve_local_overrides
from scripts.run_hvac_doclevel_extraction_batch import (
    SourceItem,
    anchor_candidates,
    build_backend_llm_audit_recorder,
    build_candidate_file_payload,
    build_run_summary,
    judge_entries,
    render_report,
    task_complete_for_backends,
    task_status_from_backend_results,
)


def test_anchor_candidates_matches_verbatim_quote_to_chunk() -> None:
    chunk = ContentChunk(
        chunk_id="chunk_1",
        doc_id="doc_1",
        page_id="page_1",
        page_no=7,
        chunk_index=0,
        cleaned_text="故障代码 E01：水流开关保护。检查水泵和水流开关。",
        text_excerpt="故障代码 E01",
        chunk_type="paragraph",
    )
    page = DocumentPage(page_id="page_1", doc_id="doc_1", page_no=7, cleaned_text=chunk.cleaned_text, page_type="text")
    candidate = {
        "knowledge_type": "fault_code",
        "title": "E01 水流开关保护",
        "summary": "E01 indicates water flow switch protection.",
        "structured_payload": {"fault_code": "E01"},
        "evidence_quote": "故障代码 E01：水流开关保护",
        "confidence": 0.91,
    }

    anchored, rejected = anchor_candidates([candidate], [(chunk, page, object())])

    assert rejected == []
    assert anchored[0]["chunk_id"] == "chunk_1"
    assert anchored[0]["page_no"] == 7
    assert anchored[0]["trust_level"] == "L3"


def test_render_report_includes_backend_comparison_table() -> None:
    summary = {
        "run_id": "run_1",
        "output_dir": "/tmp/run_1",
        "tasks": [
            {
                "file_name": "manual.pdf",
                "doc_id": "doc_1",
                "equipment_class_id": "chiller",
                "backend_results": [
                    {
                        "backend": "deepseek-parameter-spec",
                        "status": "ok",
                        "raw_candidates": 4,
                        "anchor_passed": 3,
                        "anchor_match_rate": 75.0,
                        "by_type": {"parameter_spec": 2, "fault_code": 1},
                        "elapsed_seconds": 12.3,
                        "cost_rmb": 0.02,
                    }
                ],
            }
        ],
    }

    report = render_report(summary)

    assert "# HVAC Doc-Level Extraction Batch Report" in report
    assert "manual.pdf" in report
    assert "deepseek-parameter-spec" in report
    assert "parameter_spec:2" in report


def test_backend_config_resolves_mimo_local_overrides(monkeypatch) -> None:
    monkeypatch.delenv("MIMO_API_KEY", raising=False)
    monkeypatch.delenv("MIMO_API_BASE_URL", raising=False)
    item = {
        "name": "mimo-v2.5-pro",
        "api_base_url": "https://default.example/v1",
        "api_base_url_env": "MIMO_API_BASE_URL",
        "api_key_env": "MIMO_API_KEY",
    }

    resolved = resolve_local_overrides(
        item,
        {
            "MIMO_API_BASE_URL": "https://token-plan-sgp.xiaomimimo.com/v1",
            "MIMO_API_KEY": "local-key",
        },
    )

    assert resolved["api_base_url"] == "https://token-plan-sgp.xiaomimimo.com/v1"
    assert resolved["api_key"] == "local-key"


def test_backend_config_resolves_deepseek_from_same_local_env(monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    item = {
        "name": "deepseek-parameter-spec",
        "api_base_url": "https://api.deepseek.com",
        "api_base_url_env": "DEEPSEEK_API_BASE_URL",
        "api_key_env": "DEEPSEEK_API_KEY",
    }

    resolved = resolve_local_overrides(
        item,
        {
            "DEEPSEEK_API_BASE_URL": "https://api.deepseek.com",
            "DEEPSEEK_API_KEY": "deepseek-key",
        },
    )

    assert resolved["api_base_url"] == "https://api.deepseek.com"
    assert resolved["api_key"] == "deepseek-key"


def test_task_complete_requires_all_requested_backends_ok() -> None:
    task = {
        "status": "completed",
        "backend_results": [
            {"backend": "deepseek-parameter-spec", "status": "ok"},
            {"backend": "mimo-v2.5-pro", "status": "failed"},
        ],
    }

    assert not task_complete_for_backends(task, ["deepseek-parameter-spec", "mimo-v2.5-pro"])
    assert task_complete_for_backends(task, ["deepseek-parameter-spec"])


def test_task_status_fails_when_all_backends_fail() -> None:
    assert task_status_from_backend_results([{"backend": "deepseek-v4-pro", "status": "failed"}]) == "failed"
    assert task_status_from_backend_results([{"backend": "deepseek-v4-pro", "status": "ok"}]) == "completed"


def test_task_complete_requires_judge_when_requested() -> None:
    task = {
        "status": "completed",
        "backend_results": [
            {"backend": "deepseek-parameter-spec", "status": "ok", "judge_enabled": False},
        ],
    }

    assert task_complete_for_backends(task, ["deepseek-parameter-spec"])
    assert not task_complete_for_backends(task, ["deepseek-parameter-spec"], "deepseek-v4-pro")


def test_judge_entries_splits_accepted_and_rejected(monkeypatch) -> None:
    def fake_request(messages, backend, response_format=None, recorder=None):
        payload = {"response": {"usage": {"prompt_tokens": 10, "completion_tokens": 5}}}
        if recorder:
            recorder(payload)
        return {
            "verdicts": [
                {"candidate_id": "cand_ok", "is_valid_hvac_knowledge": True, "reason": "Grounded fault code."},
                {
                    "candidate_id": "cand_bad",
                    "is_valid_hvac_knowledge": False,
                    "reason": "Only a terminal label.",
                    "category_if_not": "terminal_label",
                },
            ]
        }

    monkeypatch.setattr("scripts.run_hvac_doclevel_extraction_batch._request_json_completion", fake_request)
    backend = OpenAICompatibleBackend(name="judge", api_base_url="https://example.test/v1", model="judge-model", api_key="key")
    doc = Document(doc_id="doc_1", file_name="manual.pdf", source_domain="hvac", file_hash="hash", storage_path="/tmp/manual.pdf")
    equipment = {"equipment_class_id": "chiller"}
    entries = [
        _judge_entry("cand_ok", "fault_code", "E01"),
        _judge_entry("cand_bad", "parameter_spec", "X1"),
    ]

    accepted, rejected, raw = judge_entries(entries, backend, doc, equipment)

    assert [row["candidate_id"] for row in accepted] == ["cand_ok"]
    assert [row["candidate_id"] for row in rejected] == ["cand_bad"]
    assert rejected[0]["judge_category"] == "terminal_label"
    assert raw["response"]["usage"]["prompt_tokens"] == 10


def test_judge_entries_rejects_incomplete_verdict_without_failing(monkeypatch) -> None:
    def fake_request(messages, backend, response_format=None, recorder=None):
        payload = {"response": {"usage": {"prompt_tokens": 8, "completion_tokens": 2}}}
        if recorder:
            recorder(payload)
        return {"verdicts": [{"candidate_id": "cand_incomplete"}]}

    monkeypatch.setattr("scripts.run_hvac_doclevel_extraction_batch._request_json_completion", fake_request)
    backend = OpenAICompatibleBackend(name="judge", api_base_url="https://example.test/v1", model="judge-model", api_key="key")
    doc = Document(doc_id="doc_1", file_name="manual.pdf", source_domain="hvac", file_hash="hash", storage_path="/tmp/manual.pdf")
    equipment = {"equipment_class_id": "chiller"}

    accepted, rejected, raw = judge_entries([_judge_entry("cand_incomplete", "parameter_spec", "X1")], backend, doc, equipment)

    assert accepted == []
    assert rejected[0]["candidate_id"] == "cand_incomplete"
    assert rejected[0]["judge_category"] == "malformed_judge_verdict"
    assert "omitted required fields" in rejected[0]["judge_reason"]
    assert raw["response"]["usage"]["prompt_tokens"] == 8


def test_doclevel_backend_llm_recorder_writes_under_run_dir(tmp_path: Path) -> None:
    task_dir = tmp_path / "20260513T010101Z_hvac_doclevel_extraction_batch/0001_manual"
    task_dir.mkdir(parents=True)
    item = SourceItem(
        row_index=1,
        path=Path("/tmp/manual.pdf"),
        batch_group="B_oem_manual_text_first",
        priority="high",
        brand="Trane",
        authority_level="oem_manual",
        document_kind="manual",
        equipment_scope="centrifugal_chiller",
        page_count="10",
        text_quality="text",
        recommended_mode="text",
        raw={},
    )
    backend = OpenAICompatibleBackend(name="extract", api_base_url="https://example.test/v1", model="model", api_key="key")

    recorder, path = build_backend_llm_audit_recorder(
        task_dir,
        item,
        backend,
        call_site="hvac_doclevel_extract",
        date_label="20260513",
    )
    recorder({"request": {"authorization": "Bearer secret"}, "response": {"usage": {"prompt_tokens": 1}}})

    assert path == task_dir.parent / "llm_audit/20260513/20260513T010101Z_hvac_doclevel_extraction_batch.jsonl"
    row = path.read_text(encoding="utf-8")
    assert "hvac_doclevel_extract" in row
    assert "manual.pdf" in row
    assert "secret" not in row


def test_doclevel_summary_includes_compiler_run_and_source_manifest(tmp_path: Path) -> None:
    source_path = tmp_path / "manual.pdf"
    source_path.write_bytes(b"%PDF-1.4 source")
    item = SourceItem(
        row_index=1,
        path=source_path,
        batch_group="B_oem_manual_text_first",
        priority="high",
        brand="Trane",
        authority_level="oem_manual",
        document_kind="manual",
        equipment_scope="centrifugal_chiller",
        page_count="10",
        text_quality="text",
        recommended_mode="text",
        raw={},
    )
    batch_dir = tmp_path / "20260513T010101Z_hvac_doclevel_extraction_batch"

    summary = build_run_summary(
        batch_dir=batch_dir,
        items=[item],
        tasks=[],
        parameters={"backends": ["extract"], "judge_backend": ""},
    )

    assert summary["compiler_run"]["compiler_run_id"] == batch_dir.name
    assert summary["compiler_run"]["pipeline"] == "hvac_doclevel_extraction_batch"
    assert summary["compiler_run"]["parameters"]["backends"] == ["extract"]
    assert summary["source_manifest"][0]["source_type"] == "document"
    assert summary["source_manifest"][0]["domain_id"] == "hvac"
    assert summary["source_manifest"][0]["authority_levels"] == ["oem_manual"]
    assert summary["source_manifest"][0]["metadata"]["brand"] == "Trane"
    assert len(summary["source_manifest"][0]["content_sha256"]) == 64


def test_doclevel_summary_records_missing_source_without_crashing(tmp_path: Path) -> None:
    item = SourceItem(
        row_index=1,
        path=tmp_path / "missing.pdf",
        batch_group="B_oem_manual_text_first",
        priority="high",
        brand="Trane",
        authority_level="oem_manual",
        document_kind="manual",
        equipment_scope="centrifugal_chiller",
        page_count="10",
        text_quality="text",
        recommended_mode="text",
        raw={},
    )

    summary = build_run_summary(
        batch_dir=tmp_path / "run_missing",
        items=[item],
        tasks=[],
        parameters={"backends": ["extract"]},
    )

    source = summary["source_manifest"][0]
    assert source["source_id"] == "missing"
    assert source["content_sha256"] == ""
    assert "source file not found" in source["metadata"]["manifest_error"]


def test_doclevel_candidate_payload_includes_compiler_run() -> None:
    payload = build_candidate_file_payload(
        entries=[],
        backend_dir=Path("/tmp/run_001/0001_manual/extract"),
        source_manifest=[
            {
                "source_id": "manual",
                "source_type": "document",
                "path": "/tmp/manual.pdf",
                "content_sha256": "a" * 64,
            }
        ],
    )

    assert payload["generation_mode"] == "llm_doclevel_batch"
    assert payload["compiler_run"]["compiler_run_id"] == "run_001"
    assert payload["compiler_run"]["pipeline"] == "hvac_doclevel_extraction_batch"
    assert payload["source_manifest"][0]["content_sha256"] == "a" * 64


def _judge_entry(candidate_id: str, ko_type: str, title: str) -> dict:
    return {
        "candidate_id": candidate_id,
        "knowledge_object_type": ko_type,
        "structured_payload_candidate": {"title": title, "summary": f"{title} summary"},
        "evidence_text": f"{title} evidence",
        "source_page_nos": [1],
        "trust_level": "L3",
    }
