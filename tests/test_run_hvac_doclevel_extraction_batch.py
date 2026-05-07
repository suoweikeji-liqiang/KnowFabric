"""Tests for document-level HVAC extraction batch helpers."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.models import ContentChunk, DocumentPage
from scripts.llm_backend_config import resolve_local_overrides
from scripts.run_hvac_doclevel_extraction_batch import anchor_candidates, render_report, task_complete_for_backends


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
