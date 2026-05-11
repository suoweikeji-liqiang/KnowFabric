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


def _entry_evidence_refs(entry: dict[str, Any]) -> list[dict[str, Any]]:
    refs = [entry]
    refs.extend(item for item in entry.get("additional_evidence", []) if isinstance(item, dict))
    return refs


def _build_fixture_base_rows(
    fixture: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    document_rows: dict[str, dict[str, Any]] = {}
    page_rows: dict[str, dict[str, Any]] = {}
    chunk_rows: dict[str, dict[str, Any]] = {}
    chunk_contexts: dict[str, dict[str, Any]] = {}

    for entry in fixture["manual_entries"]:
        for evidence_ref in _entry_evidence_refs(entry):
            doc_id = evidence_ref["doc"]["doc_id"]
            page_id = evidence_ref["page"]["page_id"]
            page_no = evidence_ref["page"]["page_no"]
            chunk_id = evidence_ref["chunk"]["chunk_id"]

            document_rows[doc_id] = {
                "doc_id": doc_id,
                "file_hash": f"hash_{doc_id}",
                "storage_path": evidence_ref["source_manual"]["path"],
                "file_name": evidence_ref["doc"]["file_name"],
                "file_ext": "pdf",
                "mime_type": "application/pdf",
                "file_size": 1,
                "source_domain": evidence_ref["doc"]["source_domain"],
                "parse_status": "complete",
                "is_active": True,
            }
            page_rows[page_id] = {
                "page_id": page_id,
                "doc_id": doc_id,
                "page_no": page_no,
                "raw_text": evidence_ref["evidence"]["evidence_text"],
                "cleaned_text": evidence_ref["evidence"]["evidence_text"],
                "page_type": evidence_ref["page"]["page_type"],
            }
            chunk_rows[chunk_id] = {
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "page_id": page_id,
                "page_no": page_no,
                "chunk_index": evidence_ref["chunk"]["chunk_index"],
                "raw_text": evidence_ref["chunk"]["cleaned_text"],
                "cleaned_text": evidence_ref["chunk"]["cleaned_text"],
                "text_excerpt": evidence_ref["chunk"]["text_excerpt"],
                "chunk_type": evidence_ref["chunk"]["chunk_type"],
                "evidence_anchor": json.dumps({"manual_page": evidence_ref["source_manual"]["page_no"]}, ensure_ascii=False),
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
    evidence_ref: dict[str, Any] | None = None,
) -> dict[str, Any]:
    evidence_ref = evidence_ref or entry
    chunk_id = evidence_ref["chunk"]["chunk_id"]
    anchor_id = f'anchor_{entry["knowledge_object_id"]}'
    if chunk_id != entry["chunk"]["chunk_id"]:
        anchor_id = f'anchor_{entry["knowledge_object_id"]}_{chunk_id[-12:]}'
    return {
        "chunk_anchor_id": anchor_id,
        "chunk_id": chunk_id,
        "ontology_class_key": fixture["equipment_class_key"],
        "domain_id": fixture["domain_id"],
        "ontology_class_id": fixture["equipment_class_id"],
        "match_method": match_method,
        "confidence_score": entry["confidence_score"],
        "is_primary": True,
        "match_metadata_json": {
            "source_manual": evidence_ref["source_manual"]["path"],
            "source_manual_page_no": evidence_ref["source_manual"]["page_no"],
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
        "curated_against_ontology_version": entry.get("curated_against_ontology_version"),
        "authority_summary_json": entry.get("authority_summary_json"),
        "consensus_state": entry.get("consensus_state", "single_source"),
        "conflict_summary": entry.get("conflict_summary"),
        "highest_authority_level": entry.get("highest_authority_level"),
        "deviation_justification_json": entry.get("deviation_justification_json"),
    }


def _build_evidence_row(entry: dict[str, Any], evidence_ref: dict[str, Any], chunk_context: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "knowledge_evidence_id": evidence_ref["evidence"]["knowledge_evidence_id"],
        "knowledge_object_id": entry["knowledge_object_id"],
        "chunk_id": evidence_ref["chunk"]["chunk_id"],
        "doc_id": chunk_context["doc_id"],
        "page_id": chunk_context["page_id"],
        "page_no": chunk_context["page_no"],
        "evidence_text": evidence_ref["evidence"]["evidence_text"],
        "evidence_role": evidence_ref["evidence"]["evidence_role"],
        "authority_role": evidence_ref["evidence"].get("authority_role"),
        "evidence_citation": evidence_ref["evidence"].get("evidence_citation"),
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
        for evidence_ref in _entry_evidence_refs(entry):
            chunk_id = evidence_ref["chunk"]["chunk_id"]
            chunk_context = chunk_contexts.get(chunk_id)
            if chunk_context is None:
                raise ValueError(f"Missing chunk context for manual entry: {chunk_id}")
            _validate_chunk_context(evidence_ref, chunk_context)
            anchor_rows.append(_build_anchor_row(fixture, entry, match_method=match_method, evidence_ref=evidence_ref))
            evidence_rows.append(_build_evidence_row(entry, evidence_ref, chunk_context))
        knowledge_rows.append(
            _build_knowledge_row(
                fixture,
                entry,
                package_version=package_version,
                ontology_version=ontology_version,
            )
        )

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
