#!/usr/bin/env python3
"""Generate review candidates for chunk-backed semantic backfill."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session

from packages.compiler.equipment_matcher import (
    build_equipment_profiles,
    build_search_text,
    match_equipment_class,
)
from packages.compiler.llm_compiler import (
    DEFAULT_LLM_ENABLED_TYPES,
    OpenAICompatibleBackend,
    build_context_window,
    compile_llm_candidates,
)
from packages.compiler.rule_compiler import (
    detect_rule_knowledge_candidates,
    short_text,
    stable_candidate_id,
)
from packages.db.models import ContentChunk, Document, DocumentPage
from packages.db.session import SessionLocal
from packages.health.checks import candidate_health_findings


def _load_chunk_rows(
    db: Session,
    domain_id: str,
    doc_id: str | None,
    chunk_id: str | None,
) -> list[tuple[ContentChunk, DocumentPage, Document]]:
    query = (
        db.query(ContentChunk, DocumentPage, Document)
        .join(DocumentPage, ContentChunk.page_id == DocumentPage.page_id)
        .join(Document, ContentChunk.doc_id == Document.doc_id)
        .filter(Document.source_domain == domain_id)
        .order_by(ContentChunk.doc_id, ContentChunk.page_no, ContentChunk.chunk_index)
    )
    if doc_id:
        query = query.filter(ContentChunk.doc_id == doc_id)
    if chunk_id:
        query = query.filter(ContentChunk.chunk_id == chunk_id)
    return query.all()


def _merge_compiler_candidates(*candidate_lists: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for candidates in candidate_lists:
        for candidate in candidates:
            key = (
                str(candidate["knowledge_object_type"]),
                str(candidate["canonical_key_candidate"]),
            )
            existing = merged.get(key)
            if existing is None:
                merged[key] = candidate
                continue
            current_method = candidate.get("compile_metadata", {}).get("method")
            previous_method = existing.get("compile_metadata", {}).get("method")
            if current_method == "llm_compiler" and previous_method != "llm_compiler":
                merged[key] = candidate
                continue
            if float(candidate.get("confidence_score") or 0.0) > float(existing.get("confidence_score") or 0.0):
                merged[key] = candidate
    return list(merged.values())


def _build_candidate_entry(
    domain_id: str,
    chunk: ContentChunk,
    page: DocumentPage,
    document: Document,
    equipment_match: dict[str, Any],
    alternatives: list[dict[str, Any]],
    knowledge_candidate: dict[str, Any],
) -> dict[str, Any]:
    candidate_id = stable_candidate_id(
        domain_id,
        chunk.chunk_id,
        equipment_match["equipment_class_key"],
        knowledge_candidate["knowledge_object_type"],
        knowledge_candidate["canonical_key_candidate"],
    )
    entry = {
        "candidate_id": candidate_id,
        "domain_id": domain_id,
        "doc_id": document.doc_id,
        "doc_name": document.file_name,
        "page_id": page.page_id,
        "page_no": page.page_no,
        "chunk_id": chunk.chunk_id,
        "chunk_index": chunk.chunk_index,
        "chunk_type": chunk.chunk_type,
        "page_type": page.page_type,
        "text_excerpt": chunk.text_excerpt or short_text(chunk.cleaned_text),
        "evidence_text": short_text(chunk.cleaned_text),
        "equipment_class_candidate": {
            "equipment_class_id": equipment_match["equipment_class_id"],
            "equipment_class_key": equipment_match["equipment_class_key"],
            "label": equipment_match["label"],
            "confidence": equipment_match["confidence"],
            "matched_aliases": equipment_match["matched_aliases"],
            "supported_knowledge_anchors": list(equipment_match.get("knowledge_anchors", [])),
        },
        "knowledge_object_type": knowledge_candidate["knowledge_object_type"],
        "canonical_key_candidate": knowledge_candidate["canonical_key_candidate"],
        "structured_payload_candidate": knowledge_candidate["structured_payload_candidate"],
        "confidence_score": knowledge_candidate["confidence_score"],
        "review_status": "candidate",
        "match_metadata": {
            "equipment_selection_method": equipment_match["selection_method"],
            "alternative_equipment_class_candidates": alternatives,
            "knowledge_signal": knowledge_candidate["knowledge_signal"],
        },
        "compile_metadata": knowledge_candidate.get("compile_metadata", {}),
        "health_findings": [],
    }
    entry["health_findings"] = candidate_health_findings(entry)
    return entry


def _build_doc_summaries(
    rows: list[tuple[ContentChunk, DocumentPage, Document]],
    entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    scanned: dict[str, dict[str, Any]] = {}
    matched_chunks_by_doc: defaultdict[str, set[str]] = defaultdict(set)
    candidate_counts: Counter[str] = Counter()

    for _, _, document in rows:
        scanned.setdefault(
            document.doc_id,
            {"doc_id": document.doc_id, "doc_name": document.file_name, "scanned_chunks": 0},
        )
        scanned[document.doc_id]["scanned_chunks"] += 1

    for entry in entries:
        matched_chunks_by_doc[entry["doc_id"]].add(entry["chunk_id"])
        candidate_counts[entry["doc_id"]] += 1

    summaries = []
    for doc_id, info in sorted(scanned.items()):
        scanned_chunks = info["scanned_chunks"]
        matched_chunks = len(matched_chunks_by_doc.get(doc_id, set()))
        summaries.append(
            {
                "doc_id": doc_id,
                "doc_name": info["doc_name"],
                "scanned_chunks": scanned_chunks,
                "matched_chunks": matched_chunks,
                "candidate_entries": candidate_counts.get(doc_id, 0),
                "candidate_hit_rate": round((matched_chunks / scanned_chunks), 3) if scanned_chunks else 0.0,
            }
        )
    return summaries


def generate_chunk_backfill_candidates(
    domain_id: str,
    *,
    doc_id: str | None = None,
    chunk_id: str | None = None,
    equipment_class_id: str | None = None,
    limit: int = 100,
    llm_backend: OpenAICompatibleBackend | None = None,
    enable_llm: bool = True,
    llm_enabled_types: tuple[str, ...] | list[str] | None = None,
) -> dict[str, Any]:
    """Generate review candidates from existing chunk rows."""

    session = SessionLocal()
    try:
        profiles = build_equipment_profiles(session, domain_id)
        rows = _load_chunk_rows(session, domain_id, doc_id, chunk_id)
        entries = []
        for index, (chunk, page, document) in enumerate(rows):
            equipment_match, alternatives = match_equipment_class(
                profiles,
                build_search_text(chunk, document),
                equipment_class_id,
            )
            if equipment_match is None:
                continue
            rule_candidates = detect_rule_knowledge_candidates(chunk, page, equipment_match)
            llm_candidates = (
                compile_llm_candidates(
                    domain_id=domain_id,
                    chunk=chunk,
                    page=page,
                    document=document,
                    equipment_match=equipment_match,
                    context_window=build_context_window(rows, index),
                    backend=llm_backend,
                    enabled_types=llm_enabled_types or DEFAULT_LLM_ENABLED_TYPES,
                )
                if enable_llm
                else []
            )
            for knowledge_candidate in _merge_compiler_candidates(rule_candidates, llm_candidates):
                entries.append(
                    _build_candidate_entry(
                        domain_id,
                        chunk,
                        page,
                        document,
                        equipment_match,
                        alternatives,
                        knowledge_candidate,
                    )
                )
        entries.sort(key=lambda item: (-item["confidence_score"], item["doc_id"], item["page_no"], item["chunk_index"]))
        limited = entries[:limit]
        matched_chunks = len({entry["chunk_id"] for entry in limited})
        doc_summaries = _build_doc_summaries(rows, limited)
        compiler_methods = sorted(
            {
                entry.get("compile_metadata", {}).get("method", "unknown")
                for entry in limited
            }
        )
        health_codes = Counter(
            finding["code"]
            for entry in limited
            for finding in entry.get("health_findings", [])
        )
        return {
            "generation_mode": "chunk_backfill_review_candidate",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "domain_id": domain_id,
            "filters_applied": {
                "doc_id": doc_id,
                "chunk_id": chunk_id,
                "equipment_class_id": equipment_class_id,
                "limit": limit,
            },
            "candidate_entries": limited,
            "metadata": {
                "total_candidates": len(limited),
                "scanned_chunks": len(rows),
                "matched_chunks": matched_chunks,
                "candidate_hit_rate": round((matched_chunks / len(rows)), 3) if rows else 0.0,
                "candidate_knowledge_types": sorted({item["knowledge_object_type"] for item in limited}),
                "compiler_methods": compiler_methods,
                "health_finding_counts": dict(health_codes),
                "doc_summaries": doc_summaries,
            },
        }
    finally:
        session.close()


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("domain_id", help="Domain scope such as 'hvac' or 'drive'")
    parser.add_argument("--doc-id", dest="doc_id", help="Limit candidate generation to one document")
    parser.add_argument("--chunk-id", dest="chunk_id", help="Limit candidate generation to one chunk")
    parser.add_argument(
        "--equipment-class-id",
        dest="equipment_class_id",
        help="Optional known equipment class to avoid ambiguous alias matching",
    )
    parser.add_argument("--limit", type=int, default=100, help="Maximum number of candidate entries to return")
    parser.add_argument("--output", help="Optional JSON file path for generated candidates")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    payload = generate_chunk_backfill_candidates(
        args.domain_id,
        doc_id=args.doc_id,
        chunk_id=args.chunk_id,
        equipment_class_id=args.equipment_class_id,
        limit=args.limit,
    )
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
        print(f"Wrote {payload['metadata']['total_candidates']} candidates to {args.output}")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Chunk backfill candidate generation failed: {exc}")
        raise SystemExit(1)
