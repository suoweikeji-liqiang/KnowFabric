#!/usr/bin/env python3
"""Generate operator review markdown for MANUAL_REVIEW triage documents."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.models import Document
from packages.db.session import SessionLocal


def make_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def metadata(doc: Document) -> dict[str, Any]:
    value = doc.authority_metadata_json
    return value if isinstance(value, dict) else {}


def row_for(doc: Document) -> list[str]:
    meta = metadata(doc)
    path = meta.get("source_path") or doc.storage_path
    return [
        str(doc.doc_id),
        str(doc.file_name),
        str(path),
        str(doc.authority_level or meta.get("authority_level") or ""),
        str(doc.publisher or meta.get("publisher") or ""),
        str(meta.get("document_kind") or ""),
        str(meta.get("text_quality") or ""),
        str(meta.get("page_count") or ""),
        str(doc.processing_decision_reason or ""),
        "",
    ]


def render_markdown(docs: list[Document], run_id: str) -> str:
    lines = [
        "# Manual Triage Review",
        "",
        f"- Run ID: `{run_id}`",
        f"- MANUAL_REVIEW documents: `{len(docs)}`",
        "",
        "## Operator Decisions",
        "",
        "| doc_id | file_name | path | authority_level | publisher | document_kind | text_quality | page_count | reason | operator_decision |",
        "|---|---|---|---|---|---|---|---:|---|---|",
    ]
    for doc in docs:
        lines.append("| " + " | ".join(_escape(cell) for cell in row_for(doc)) + " |")

    gb_docs = [doc for doc in docs if _is_gb_word_doc(doc)]
    if gb_docs:
        lines.extend(["", "## GB Word Standards", ""])
        for doc in gb_docs:
            lines.append(f"- `{doc.doc_id}` {doc.file_name}")

    unknown_large = [doc for doc in docs if _is_unknown_large(doc)]
    if unknown_large:
        lines.extend(["", "## Unknown Text Quality Large Documents", ""])
        for doc in unknown_large:
            meta = metadata(doc)
            lines.append(f"- `{doc.doc_id}` {doc.file_name} page_count={meta.get('page_count', '')}")
    return "\n".join(lines) + "\n"


def _escape(value: str) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _is_gb_word_doc(doc: Document) -> bool:
    name = (doc.file_name or "").lower()
    return (doc.file_ext or "").lower().lstrip(".") in {"doc", "docx"} and ("gb" in name or "gbt" in name or "标准" in name)


def _is_unknown_large(doc: Document) -> bool:
    meta = metadata(doc)
    try:
        page_count = int(float(str(meta.get("page_count") or 0)))
    except ValueError:
        page_count = 0
    return str(meta.get("text_quality") or "").lower() in {"unknown", ""} and page_count >= 50


def generate(
    output_root: Path,
    *,
    source_domain: str | None = None,
    source_batch_id: str | None = None,
    run_id: str | None = None,
) -> Path:
    run_id = run_id or make_run_id()
    db = SessionLocal()
    try:
        query = db.query(Document).filter(Document.processing_decision == "MANUAL_REVIEW")
        if source_domain:
            query = query.filter(Document.source_domain == source_domain)
        if source_batch_id:
            query = query.filter(Document.source_batch_id == source_batch_id)
        docs = query.order_by(Document.file_name).all()
        out_dir = output_root / run_id
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "MANUAL_REVIEW.md"
        path.write_text(render_markdown(docs, run_id), encoding="utf-8")
        return path
    finally:
        db.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", default="workspace/triage_review")
    parser.add_argument("--source-domain", default="hvac")
    parser.add_argument("--source-batch-id")
    parser.add_argument("--run-id")
    args = parser.parse_args(argv)
    path = generate(
        Path(args.output_root),
        source_domain=args.source_domain,
        source_batch_id=args.source_batch_id,
        run_id=args.run_id,
    )
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
