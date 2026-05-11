#!/usr/bin/env python3
"""Batch-run MiMo visual evidence extraction for low-text PDF pages.

Reads a source inventory CSV, renders pages, runs triage, calls MiMo for visual
extraction, and writes document_page_image rows. Tracks cumulative token usage
with an 8.4e8 cap. Supports resume via existing page_image_id lookup.

Usage:
    python scripts/run_visual_evidence_batch.py --inventory source_inventory.csv --dry-run
    python scripts/run_visual_evidence_batch.py --inventory source_inventory.csv --max-docs 3
    python scripts/run_visual_evidence_batch.py --inventory source_inventory.csv  # all docs
"""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.llm_compiler import resolve_backend
from packages.db.models import ContentChunk, Document, DocumentPage
from packages.db.models_v2 import DocumentPageImageV2
from packages.db.session import SessionLocal
from packages.extraction.visual import (
    CumulativeTokenCounter,
    TokenBudgetExceeded,
    extract_visual_evidence,
)
from packages.extraction.visual_triage import triage_pages

ROOT = Path(__file__).resolve().parent.parent
RENDER_SCRIPT = ROOT / "scripts" / "render_pdf_page.swift"
STORAGE_DIR = ROOT / "storage" / "page_images"
DEFAULT_OUTPUT_DIR = ROOT / "output" / "visual_evidence_batch"


def render_page(pdf_path: Path, page: int, output_png: Path) -> None:
    output_png.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["swift", str(RENDER_SCRIPT), str(pdf_path), str(page), str(output_png)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def load_inventory(path: Path) -> list[dict[str, str]]:
    rows = []
    with open(path, encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(row)
    return rows


def already_processed(session, doc_id: str, page_no: int) -> bool:
    existing = (
        session.query(DocumentPageImageV2)
        .filter(DocumentPageImageV2.doc_id == doc_id)
        .filter(DocumentPageImageV2.page_no == page_no)
        .first()
    )
    return existing is not None


def process_document(
    doc_row: dict[str, str],
    backend,
    counter: CumulativeTokenCounter,
    session,
    *,
    dry_run: bool = False,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    doc_id = doc_row.get("doc_id", "")
    text_quality = doc_row.get("text_quality") or doc_row.get("ocr_quality") or None
    pdf_path_str = doc_row.get("pdf_path") or doc_row.get("storage_path") or ""
    pdf_path = Path(pdf_path_str)
    if not pdf_path.exists():
        return {"doc_id": doc_id, "status": "skipped", "error": f"PDF not found: {pdf_path}"}

    doc = session.query(Document).filter(Document.doc_id == doc_id).first()
    if not doc:
        return {"doc_id": doc_id, "status": "skipped", "error": "Document not in DB"}

    pages = (
        session.query(DocumentPage)
        .filter(DocumentPage.doc_id == doc_id)
        .order_by(DocumentPage.page_no)
        .all()
    )
    if not pages:
        return {"doc_id": doc_id, "status": "skipped", "error": "No pages in DB"}

    # Build triage input
    page_dicts = []
    for page in pages:
        chunks = (
            session.query(ContentChunk)
            .filter(ContentChunk.doc_id == doc_id)
            .filter(ContentChunk.page_no == page.page_no)
            .all()
        )
        page_dicts.append({
            "page_no": page.page_no,
            "page_id": page.page_id,
            "chunks": chunks,
        })

    candidates = triage_pages(doc_id, page_dicts, text_quality=text_quality)
    if not candidates:
        return {"doc_id": doc_id, "status": "skipped", "reason": "no visual pages found by triage"}

    results = []
    for c in candidates:
        page_no = c["page_no"]
        page_id = c["page_id"]

        if already_processed(session, doc_id, page_no):
            results.append({"page_no": page_no, "status": "skipped", "reason": "already processed"})
            continue

        if counter.total_tokens >= counter.cap:
            results.append({"page_no": page_no, "status": "skipped", "reason": "token budget exceeded"})
            continue

        if dry_run:
            results.append({"page_no": page_no, "status": "dry_run", "suggested_type": c["suggested_image_type"]})
            continue

        image_dir = STORAGE_DIR / doc_id
        image_path = image_dir / f"page_{page_no:04d}.png"

        try:
            render_page(pdf_path, page_no, image_path)
        except subprocess.CalledProcessError as exc:
            results.append({"page_no": page_no, "status": "failed", "error": f"render: {exc}"})
            continue

        try:
            row_dict = extract_visual_evidence(
                doc_id=doc_id,
                page_id=page_id,
                page_no=page_no,
                image_path=image_path,
                backend=backend,
            )
        except Exception as exc:
            results.append({"page_no": page_no, "status": "failed", "error": str(exc)})
            continue

        row_dict.setdefault("created_at", datetime.now(timezone.utc))
        row_dict.setdefault("updated_at", datetime.now(timezone.utc))
        session.execute(DocumentPageImageV2.__table__.insert().values(**row_dict))

        results.append({
            "page_no": page_no,
            "status": "ok",
            "image_type": row_dict["image_type"],
        })

    session.commit()
    return {
        "doc_id": doc_id,
        "status": "done",
        "candidates_found": len(candidates),
        "pages_processed": [r for r in results if r["status"] == "ok"],
        "pages_skipped": [r for r in results if r["status"] != "ok"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", required=True, help="Path to source inventory CSV")
    parser.add_argument("--max-docs", type=int, default=0, help="Max docs to process (0=all)")
    parser.add_argument("--dry-run", action="store_true", help="Triage only, no MiMo calls")
    parser.add_argument("--output-dir", help="Output directory for reports")
    args = parser.parse_args(argv)

    backend = resolve_backend()
    if backend is None and not args.dry_run:
        print("ERROR: No MiMo backend configured. Set llm_backend_config_path or env vars.")
        return 1

    inventory = load_inventory(Path(args.inventory))
    low_text_rows = [
        r for r in inventory
        if (r.get("text_quality") or r.get("ocr_quality") or "") in ("low_or_no_text", "partial_text")
    ]
    print(f"Inventory: {len(inventory)} total, {len(low_text_rows)} low-text candidates")

    counter = CumulativeTokenCounter()
    session = SessionLocal()
    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    doc_results = []
    rows_to_process = low_text_rows[:args.max_docs] if args.max_docs > 0 else low_text_rows

    try:
        for i, row in enumerate(rows_to_process):
            doc_id = row.get("doc_id", f"row_{i}")
            print(f"[{i+1}/{len(rows_to_process)}] {row.get('file_name', doc_id)} ... ", end="", flush=True)
            start = time.monotonic()
            result = process_document(
                row, backend, counter, session,
                dry_run=args.dry_run,
                output_dir=output_dir,
            )
            elapsed = time.monotonic() - start
            pages_ok = len(result.get("pages_processed", []))
            print(f"{result['status']} ({pages_ok} pages) in {elapsed:.1f}s | tokens: {counter.total_tokens:,}")
            doc_results.append(result)
    except TokenBudgetExceeded as exc:
        print(f"\nSTOPPED: {exc}")
    finally:
        session.close()

    report_path = output_dir / f"{run_id}_REPORT.md"
    lines = [
        "# Visual Evidence Batch Report",
        f"- Run: `{run_id}`",
        f"- Docs processed: {len(doc_results)}",
        f"- Total pages OK: {sum(len(r.get('pages_processed', [])) for r in doc_results)}",
        f"- Token usage: {counter.summary()}",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
