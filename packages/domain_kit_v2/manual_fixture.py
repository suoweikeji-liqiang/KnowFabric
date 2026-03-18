"""Projection helpers for manual validation fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_manual_fixture(path: str | Path) -> dict[str, Any]:
    """Load one manual validation fixture file."""

    fixture_path = Path(path)
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def discover_manual_fixture_paths(base_dir: str | Path) -> list[Path]:
    """Discover manual validation fixture JSON files."""

    root = Path(base_dir)
    return sorted(root.glob("*.json"))


def build_manual_fixture_rows(fixture: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Project one manual fixture into normalized seed row sets."""

    document_rows: dict[str, dict[str, Any]] = {}
    page_rows: dict[str, dict[str, Any]] = {}
    chunk_rows: dict[str, dict[str, Any]] = {}
    anchor_rows: list[dict[str, Any]] = []
    knowledge_rows: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []

    for entry in fixture["manual_entries"]:
        document_rows[entry["doc"]["doc_id"]] = {
            "doc_id": entry["doc"]["doc_id"],
            "file_hash": f'hash_{entry["doc"]["doc_id"]}',
            "storage_path": entry["source_manual"]["path"],
            "file_name": entry["doc"]["file_name"],
            "file_ext": "pdf",
            "mime_type": "application/pdf",
            "file_size": 1,
            "source_domain": entry["doc"]["source_domain"],
            "parse_status": "complete",
            "is_active": True,
        }
        page_rows[entry["page"]["page_id"]] = {
            "page_id": entry["page"]["page_id"],
            "doc_id": entry["doc"]["doc_id"],
            "page_no": entry["page"]["page_no"],
            "raw_text": entry["evidence"]["evidence_text"],
            "cleaned_text": entry["evidence"]["evidence_text"],
            "page_type": entry["page"]["page_type"],
        }
        chunk_rows[entry["chunk"]["chunk_id"]] = {
            "chunk_id": entry["chunk"]["chunk_id"],
            "doc_id": entry["doc"]["doc_id"],
            "page_id": entry["page"]["page_id"],
            "page_no": entry["page"]["page_no"],
            "chunk_index": entry["chunk"]["chunk_index"],
            "raw_text": entry["chunk"]["cleaned_text"],
            "cleaned_text": entry["chunk"]["cleaned_text"],
            "text_excerpt": entry["chunk"]["text_excerpt"],
            "chunk_type": entry["chunk"]["chunk_type"],
            "evidence_anchor": json.dumps({"manual_page": entry["source_manual"]["page_no"]}, ensure_ascii=False),
        }
        anchor_rows.append(
            {
                "chunk_anchor_id": f'anchor_{entry["knowledge_object_id"]}',
                "chunk_id": entry["chunk"]["chunk_id"],
                "ontology_class_key": fixture["equipment_class_key"],
                "domain_id": fixture["domain_id"],
                "ontology_class_id": fixture["equipment_class_id"],
                "match_method": "manual_validation",
                "confidence_score": entry["confidence_score"],
                "is_primary": True,
                "match_metadata_json": {"source_manual": entry["source_manual"]["path"]},
            }
        )
        knowledge_rows.append(
            {
                "knowledge_object_id": entry["knowledge_object_id"],
                "domain_id": fixture["domain_id"],
                "ontology_class_key": fixture["equipment_class_key"],
                "ontology_class_id": fixture["equipment_class_id"],
                "knowledge_object_type": entry.get("knowledge_object_type", "fault_code"),
                "canonical_key": entry["canonical_key"],
                "title": entry["title"],
                "summary": entry["summary"],
                "structured_payload_json": entry["structured_payload"],
                "applicability_json": entry["applicability"],
                "confidence_score": entry["confidence_score"],
                "trust_level": entry["trust_level"],
                "review_status": entry["review_status"],
                "primary_chunk_id": entry["chunk"]["chunk_id"],
                "package_version": "2.0.0-alpha",
                "ontology_version": "2.0.0-alpha",
            }
        )
        evidence_rows.append(
            {
                "knowledge_evidence_id": entry["evidence"]["knowledge_evidence_id"],
                "knowledge_object_id": entry["knowledge_object_id"],
                "chunk_id": entry["chunk"]["chunk_id"],
                "doc_id": entry["doc"]["doc_id"],
                "page_id": entry["page"]["page_id"],
                "page_no": entry["page"]["page_no"],
                "evidence_text": entry["evidence"]["evidence_text"],
                "evidence_role": entry["evidence"]["evidence_role"],
                "confidence_score": entry["confidence_score"],
            }
        )

    return {
        "documents": list(document_rows.values()),
        "pages": list(page_rows.values()),
        "chunks": list(chunk_rows.values()),
        "anchors": anchor_rows,
        "knowledge_objects": knowledge_rows,
        "evidence": evidence_rows,
    }
