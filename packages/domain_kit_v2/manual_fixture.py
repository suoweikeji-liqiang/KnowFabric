"""Projection helpers for manual validation fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from packages.compiler.contracts import attach_internal_metadata

DEFAULT_PACKAGE_VERSION = "2.0.0-alpha"
DEFAULT_ONTOLOGY_VERSION = "2.0.0-alpha"


def load_manual_fixture(path: str | Path) -> dict[str, Any]:
    """Load one manual validation fixture file."""

    fixture_path = Path(path)
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def discover_manual_fixture_paths(base_dir: str | Path) -> list[Path]:
    """Discover manual validation fixture JSON files."""

    root = Path(base_dir)
    return sorted(root.glob("*.json"))


def _build_chunk_context(doc_id: str, page_id: str, page_no: int) -> dict[str, Any]:
    return {"doc_id": doc_id, "page_id": page_id, "page_no": page_no}


def _build_fixture_base_rows(
    fixture: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    document_rows: dict[str, dict[str, Any]] = {}
    page_rows: dict[str, dict[str, Any]] = {}
    chunk_rows: dict[str, dict[str, Any]] = {}
    chunk_contexts: dict[str, dict[str, Any]] = {}

    for entry in fixture["manual_entries"]:
        doc_id = entry["doc"]["doc_id"]
        page_id = entry["page"]["page_id"]
        page_no = entry["page"]["page_no"]
        chunk_id = entry["chunk"]["chunk_id"]

        document_rows[doc_id] = {
            "doc_id": doc_id,
            "file_hash": f"hash_{doc_id}",
            "storage_path": entry["source_manual"]["path"],
            "file_name": entry["doc"]["file_name"],
            "file_ext": "pdf",
            "mime_type": "application/pdf",
            "file_size": 1,
            "source_domain": entry["doc"]["source_domain"],
            "parse_status": "complete",
            "is_active": True,
        }
        page_rows[page_id] = {
            "page_id": page_id,
            "doc_id": doc_id,
            "page_no": page_no,
            "raw_text": entry["evidence"]["evidence_text"],
            "cleaned_text": entry["evidence"]["evidence_text"],
            "page_type": entry["page"]["page_type"],
        }
        chunk_rows[chunk_id] = {
            "chunk_id": chunk_id,
            "doc_id": doc_id,
            "page_id": page_id,
            "page_no": page_no,
            "chunk_index": entry["chunk"]["chunk_index"],
            "raw_text": entry["chunk"]["cleaned_text"],
            "cleaned_text": entry["chunk"]["cleaned_text"],
            "text_excerpt": entry["chunk"]["text_excerpt"],
            "chunk_type": entry["chunk"]["chunk_type"],
            "evidence_anchor": json.dumps({"manual_page": entry["source_manual"]["page_no"]}, ensure_ascii=False),
        }
        chunk_contexts[chunk_id] = _build_chunk_context(doc_id, page_id, page_no)

    return document_rows, page_rows, chunk_rows, chunk_contexts


def _validate_chunk_context(entry: dict[str, Any], chunk_context: Mapping[str, Any]) -> None:
    expected = _build_chunk_context(
        entry["doc"]["doc_id"],
        entry["page"]["page_id"],
        entry["page"]["page_no"],
    )
    actual = {key: chunk_context[key] for key in expected}
    if actual != expected:
        raise ValueError(
            f'Chunk chain mismatch for {entry["chunk"]["chunk_id"]}: '
            f"expected {expected}, got {actual}"
        )


def _build_anchor_row(
    fixture: dict[str, Any],
    entry: dict[str, Any],
    *,
    match_method: str,
) -> dict[str, Any]:
    return {
        "chunk_anchor_id": f'anchor_{entry["knowledge_object_id"]}',
        "chunk_id": entry["chunk"]["chunk_id"],
        "ontology_class_key": fixture["equipment_class_key"],
        "domain_id": fixture["domain_id"],
        "ontology_class_id": fixture["equipment_class_id"],
        "match_method": match_method,
        "confidence_score": entry["confidence_score"],
        "is_primary": True,
        "match_metadata_json": {
            "source_manual": entry["source_manual"]["path"],
            "source_manual_page_no": entry["source_manual"]["page_no"],
        },
    }


def _build_knowledge_row(
    fixture: dict[str, Any],
    entry: dict[str, Any],
    *,
    package_version: str,
    ontology_version: str,
) -> dict[str, Any]:
    structured_payload = attach_internal_metadata(
        dict(entry["structured_payload"]),
        compile_metadata=entry.get("compiler_metadata"),
        health_signals=entry.get("health_signals"),
    )
    localized_display = entry.get("localized_display")
    if localized_display:
        structured_payload["_localized_display"] = localized_display
    return {
        "knowledge_object_id": entry["knowledge_object_id"],
        "domain_id": fixture["domain_id"],
        "ontology_class_key": fixture["equipment_class_key"],
        "ontology_class_id": fixture["equipment_class_id"],
        "knowledge_object_type": entry.get("knowledge_object_type", "fault_code"),
        "canonical_key": entry["canonical_key"],
        "title": entry["title"],
        "summary": entry["summary"],
        "structured_payload_json": structured_payload,
        "applicability_json": entry["applicability"],
        "confidence_score": entry["confidence_score"],
        "trust_level": entry["trust_level"],
        "review_status": entry["review_status"],
        "primary_chunk_id": entry["chunk"]["chunk_id"],
        "package_version": package_version,
        "ontology_version": ontology_version,
    }


def _build_evidence_row(entry: dict[str, Any], chunk_context: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "knowledge_evidence_id": entry["evidence"]["knowledge_evidence_id"],
        "knowledge_object_id": entry["knowledge_object_id"],
        "chunk_id": entry["chunk"]["chunk_id"],
        "doc_id": chunk_context["doc_id"],
        "page_id": chunk_context["page_id"],
        "page_no": chunk_context["page_no"],
        "evidence_text": entry["evidence"]["evidence_text"],
        "evidence_role": entry["evidence"]["evidence_role"],
        "confidence_score": entry["confidence_score"],
    }


def build_manual_semantic_rows(
    fixture: dict[str, Any],
    *,
    package_version: str,
    ontology_version: str,
    chunk_contexts: Mapping[str, Mapping[str, Any]],
    match_method: str,
) -> dict[str, list[dict[str, Any]]]:
    """Project manual curation into anchors, knowledge objects, and evidence rows."""

    anchor_rows: list[dict[str, Any]] = []
    knowledge_rows: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []

    for entry in fixture["manual_entries"]:
        chunk_id = entry["chunk"]["chunk_id"]
        chunk_context = chunk_contexts.get(chunk_id)
        if chunk_context is None:
            raise ValueError(f"Missing chunk context for manual entry: {chunk_id}")
        _validate_chunk_context(entry, chunk_context)
        anchor_rows.append(_build_anchor_row(fixture, entry, match_method=match_method))
        knowledge_rows.append(
            _build_knowledge_row(
                fixture,
                entry,
                package_version=package_version,
                ontology_version=ontology_version,
            )
        )
        evidence_rows.append(_build_evidence_row(entry, chunk_context))

    return {
        "anchors": anchor_rows,
        "knowledge_objects": knowledge_rows,
        "evidence": evidence_rows,
    }


def build_manual_fixture_rows(
    fixture: dict[str, Any],
    *,
    package_version: str = DEFAULT_PACKAGE_VERSION,
    ontology_version: str = DEFAULT_ONTOLOGY_VERSION,
) -> dict[str, list[dict[str, Any]]]:
    """Project one manual fixture into normalized seed row sets."""

    document_rows, page_rows, chunk_rows, chunk_contexts = _build_fixture_base_rows(fixture)
    semantic_rows = build_manual_semantic_rows(
        fixture,
        package_version=package_version,
        ontology_version=ontology_version,
        chunk_contexts=chunk_contexts,
        match_method="manual_validation",
    )
    return {
        "documents": list(document_rows.values()),
        "pages": list(page_rows.values()),
        "chunks": list(chunk_rows.values()),
        "anchors": semantic_rows["anchors"],
        "knowledge_objects": semantic_rows["knowledge_objects"],
        "evidence": semantic_rows["evidence"],
    }
