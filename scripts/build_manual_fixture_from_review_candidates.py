#!/usr/bin/env python3
"""Build a manual backfill fixture from reviewed chunk candidate JSON."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.models import ContentChunk, Document, DocumentPage
from packages.db.session import SessionLocal


def _stable_id(prefix: str, seed: str) -> str:
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _load_review_candidate_payload(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("review candidate file must contain a JSON object")
    if "candidate_entries" not in payload or not isinstance(payload["candidate_entries"], list):
        raise ValueError("review candidate file must include a candidate_entries list")
    return payload


def _accepted_entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    accepted = [
        entry
        for entry in payload["candidate_entries"]
        if entry.get("review_decision") == "accepted"
    ]
    if not accepted:
        raise ValueError("No accepted review candidates found")
    return accepted


def _require_dict(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return value


def _require_non_empty_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _get_equipment_identity(entries: list[dict[str, Any]]) -> tuple[str, str, str]:
    identities = {
        (
            entry["domain_id"],
            entry["equipment_class_candidate"]["equipment_class_id"],
            entry["equipment_class_candidate"]["equipment_class_key"],
        )
        for entry in entries
    }
    if len(identities) != 1:
        raise ValueError("Accepted review candidates must belong to exactly one equipment class")
    return identities.pop()


def _validate_candidate_chain(
    entry: dict[str, Any],
    chunk: ContentChunk,
    page: DocumentPage,
    document: Document,
) -> None:
    expected = {
        "doc_id": document.doc_id,
        "page_id": page.page_id,
        "page_no": page.page_no,
        "chunk_id": chunk.chunk_id,
    }
    actual = {
        "doc_id": entry["doc_id"],
        "page_id": entry["page_id"],
        "page_no": entry["page_no"],
        "chunk_id": entry["chunk_id"],
    }
    if actual != expected:
        raise ValueError(f"Candidate chain mismatch for {entry['candidate_id']}: expected {expected}, got {actual}")


def _load_chunk_chain(session: Session, entry: dict[str, Any]) -> tuple[ContentChunk, DocumentPage, Document]:
    row = (
        session.query(ContentChunk, DocumentPage, Document)
        .join(DocumentPage, ContentChunk.page_id == DocumentPage.page_id)
        .join(Document, ContentChunk.doc_id == Document.doc_id)
        .filter(ContentChunk.chunk_id == entry["chunk_id"])
        .one_or_none()
    )
    if row is None:
        raise ValueError(f"Missing chunk chain for accepted candidate: {entry['chunk_id']}")
    chunk, page, document = row
    _validate_candidate_chain(entry, chunk, page, document)
    if document.source_domain != entry["domain_id"]:
        raise ValueError(
            f"Candidate domain mismatch for {entry['candidate_id']}: "
            f"{entry['domain_id']} != {document.source_domain}"
        )
    return chunk, page, document


def _curation_block(entry: dict[str, Any]) -> dict[str, Any]:
    curation = _require_dict(entry.get("curation"), "curation")
    required = ("title", "summary", "structured_payload", "applicability", "trust_level")
    missing = [field for field in required if field not in curation]
    if missing:
        raise ValueError(
            f"Accepted candidate {entry['candidate_id']} is missing curation fields: {', '.join(missing)}"
        )
    curation["title"] = _require_non_empty_text(curation["title"], "curation.title")
    curation["summary"] = _require_non_empty_text(curation["summary"], "curation.summary")
    curation["trust_level"] = _require_non_empty_text(curation["trust_level"], "curation.trust_level")
    _require_dict(curation["structured_payload"], "curation.structured_payload")
    _require_dict(curation["applicability"], "curation.applicability")
    return curation


def _build_manual_entry(
    session: Session,
    entry: dict[str, Any],
) -> dict[str, Any]:
    curation = _curation_block(entry)
    chunk, page, document = _load_chunk_chain(session, entry)
    knowledge_object_id = curation.get("knowledge_object_id") or _stable_id("ko", entry["candidate_id"])
    knowledge_evidence_id = curation.get("knowledge_evidence_id") or _stable_id(
        "koev",
        f"{entry['candidate_id']}::evidence",
    )
    canonical_key = curation.get("canonical_key") or entry["canonical_key_candidate"]
    evidence_text = curation.get("evidence_text") or entry["evidence_text"]
    return {
        "knowledge_object_type": entry["knowledge_object_type"],
        "knowledge_object_id": knowledge_object_id,
        "canonical_key": canonical_key,
        "title": curation["title"],
        "summary": curation["summary"],
        "structured_payload": curation["structured_payload"],
        "applicability": curation["applicability"],
        "confidence_score": entry["confidence_score"],
        "trust_level": curation["trust_level"],
        "review_status": curation.get("review_status", "approved"),
        "compiler_metadata": entry.get("compile_metadata", {}),
        "health_signals": {
            "flags": [
                finding.get("code")
                for finding in entry.get("health_findings", [])
                if isinstance(finding, dict) and finding.get("code")
            ],
            "findings": entry.get("health_findings", []),
        },
        "doc": {
            "doc_id": document.doc_id,
            "file_name": document.file_name,
            "source_domain": document.source_domain,
        },
        "page": {
            "page_id": page.page_id,
            "page_no": page.page_no,
            "page_type": page.page_type,
        },
        "chunk": {
            "chunk_id": chunk.chunk_id,
            "chunk_index": chunk.chunk_index,
            "chunk_type": chunk.chunk_type,
            "cleaned_text": chunk.cleaned_text,
            "text_excerpt": chunk.text_excerpt,
        },
        "evidence": {
            "knowledge_evidence_id": knowledge_evidence_id,
            "evidence_role": curation.get("evidence_role", "primary"),
            "evidence_text": evidence_text,
        },
        "source_manual": {
            "path": document.storage_path,
            "page_no": page.page_no,
        },
    }


def build_manual_fixture_from_review_candidates(payload: dict[str, Any], session: Session) -> dict[str, Any]:
    """Convert accepted review candidates into one manual fixture."""

    accepted = _accepted_entries(payload)
    domain_id, equipment_class_id, equipment_class_key = _get_equipment_identity(accepted)
    manual_entries = [_build_manual_entry(session, entry) for entry in accepted]
    return {
        "domain_id": domain_id,
        "equipment_class_id": equipment_class_id,
        "equipment_class_key": equipment_class_key,
        "fixture_metadata": {
            "source_generation_mode": payload.get("generation_mode"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "accepted_candidate_count": len(manual_entries),
        },
        "manual_entries": manual_entries,
    }


def build_manual_fixture_from_review_candidate_file(path: str | Path) -> dict[str, Any]:
    """Load a reviewed candidate file and build one manual fixture JSON object."""

    payload = _load_review_candidate_payload(path)
    session = SessionLocal()
    try:
        return build_manual_fixture_from_review_candidates(payload, session)
    finally:
        session.close()


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review_candidate_path", help="Path to reviewed candidate JSON")
    parser.add_argument("--output", help="Optional output path for the generated manual fixture")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    fixture = build_manual_fixture_from_review_candidate_file(args.review_candidate_path)
    rendered = json.dumps(fixture, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
        print(f"Wrote {len(fixture['manual_entries'])} reviewed entries to {args.output}")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Review candidate fixture build failed: {exc}")
        raise SystemExit(1)
