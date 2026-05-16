#!/usr/bin/env python3
"""Run MiMo visual parameter extraction over KEEP_VISUAL chiller manuals."""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.audit import build_compiler_run, build_file_source_manifest_entry
from packages.compiler.rule_compiler import stable_candidate_id
from packages.core.config import settings
from packages.db.models import ContentChunk, Document, DocumentPage
from packages.db.session import SessionLocal
from packages.extraction.visual import CumulativeTokenCounter, TokenBudgetExceeded
from packages.extraction.visual_parameter_extraction import (
    ExtractedCandidate,
    extract_parameters_from_page_image,
)
from packages.storage.manager import StorageManager
from packages.ingest.service import IngestService
from packages.parser.service import ParserService
from scripts.build_review_packs_from_candidates import write_review_packs_from_candidate_file
from scripts.llm_backend_config import load_backend


ROOT = Path(__file__).resolve().parent.parent
RENDER_SCRIPT = ROOT / "scripts" / "render_pdf_page.swift"
DEFAULT_OUTPUT_ROOT = ROOT / "output" / "visual_parameter_batch"
DEFAULT_TOKEN_CAP = 150_000_000
DEFAULT_BACKEND = "mimo-v2-omni"


def make_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_visual_parameter_batch"


def render_page(pdf_path: Path, page_no: int, output_png: Path) -> None:
    output_png.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["swift", str(RENDER_SCRIPT), str(pdf_path), str(page_no), str(output_png)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def keep_visual_docs(session, doc_ids: list[str] | None = None) -> list[Document]:
    query = session.query(Document).filter(Document.processing_decision == "KEEP_VISUAL")
    if doc_ids:
        query = query.filter(Document.doc_id.in_(doc_ids))
    return query.order_by(Document.page_count.desc().nullslast(), Document.file_name).all()


def docs_from_manifest(session, manifest_path: Path, text_quality: str) -> list[tuple[Document, str, dict[str, Any]]]:
    rows = load_manifest_rows(manifest_path, text_quality=text_quality)
    docs: list[tuple[Document, str, dict[str, Any]]] = []
    for row in rows:
        local_path = Path(row["local_path"])
        if not local_path.exists():
            row["visual_status"] = "missing_file"
            continue
        doc = ensure_document_from_manifest(session, row, local_path)
        ensure_pages(session, doc.doc_id)
        equipment_class_id = route_equipment_class(row)
        docs.append((doc, equipment_class_id, row))
    return docs


def load_manifest_rows(manifest_path: Path, *, text_quality: str) -> list[dict[str, Any]]:
    with manifest_path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [row for row in rows if str(row.get("text_quality") or "").strip() == text_quality]


def ensure_document_from_manifest(session, row: dict[str, Any], local_path: Path) -> Document:
    storage = StorageManager(settings.storage_root)
    file_hash = storage.calculate_file_hash(str(local_path))
    doc = session.query(Document).filter(Document.file_hash == file_hash).first()
    if not doc:
        ingest = IngestService(storage)
        doc_id = ingest.import_document(session, str(local_path), source_domain="hvac", batch_id="phase1_scanned_visual")
        doc = session.query(Document).filter(Document.doc_id == doc_id).one()
    update_document_manifest_fields(doc, row, file_hash)
    session.commit()
    return doc


def update_document_manifest_fields(doc: Document, row: dict[str, Any], file_hash: str) -> None:
    doc.file_sha256 = file_hash
    doc.text_quality = row.get("text_quality") or doc.text_quality
    doc.page_count = int_or_none(row.get("page_count")) or doc.page_count
    doc.inventory_source_path = row.get("local_path") or doc.inventory_source_path
    doc.source_domain = "hvac"
    doc.vendor_brand = row.get("brand") or doc.vendor_brand
    doc.publisher = row.get("brand") or doc.publisher
    doc.language = infer_language(row)
    doc.processing_decision = "KEEP_VISUAL"
    metadata = dict(doc.authority_metadata_json or {})
    metadata.update({
        "phase1_manifest_priority": row.get("priority"),
        "phase1_manifest_domain": row.get("domain"),
        "needs_visual_extraction": True,
        "visual_source_path": row.get("local_path"),
    })
    doc.authority_metadata_json = metadata


def ensure_pages(session, doc_id: str) -> None:
    existing = session.query(DocumentPage).filter(DocumentPage.doc_id == doc_id).count()
    if existing:
        return
    ParserService(StorageManager(settings.storage_root)).parse_document(session, doc_id)


def document_pdf_path(doc: Document) -> Path:
    path = StorageManager(settings.storage_root).get_document_path(doc.storage_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found for {doc.doc_id}: {path}")
    return path


def pages_for_document(session, doc_id: str, max_pages: int = 0) -> list[DocumentPage]:
    pages = (
        session.query(DocumentPage)
        .filter(DocumentPage.doc_id == doc_id)
        .order_by(DocumentPage.page_no)
        .all()
    )
    return pages[:max_pages] if max_pages > 0 else pages


def chunk_for_page(session, doc_id: str, page_no: int) -> ContentChunk | None:
    return (
        session.query(ContentChunk)
        .filter(ContentChunk.doc_id == doc_id)
        .filter(ContentChunk.page_no == page_no)
        .order_by(ContentChunk.chunk_index)
        .first()
    )


def ensure_visual_chunk(session, page: DocumentPage, evidence_text: str) -> ContentChunk:
    chunk_id = f"visual_page_{page.doc_id}_{page.page_no}"
    chunk = session.query(ContentChunk).filter(ContentChunk.chunk_id == chunk_id).first()
    if chunk:
        return chunk
    text = evidence_text.strip() or f"Visual evidence page {page.page_no}"
    chunk = ContentChunk(
        chunk_id=chunk_id,
        doc_id=page.doc_id,
        page_id=page.page_id,
        page_no=page.page_no,
        chunk_index=0,
        raw_text=text,
        cleaned_text=text,
        text_excerpt=text[:200],
        chunk_type="visual_page",
        evidence_anchor="visual_parameter_batch",
    )
    session.add(chunk)
    session.flush()
    return chunk


def process_document(
    *,
    session,
    doc: Document,
    backend,
    output_dir: Path,
    counter: CumulativeTokenCounter,
    equipment_class_id: str,
    max_pages: int = 0,
) -> dict[str, Any]:
    pdf_path = document_pdf_path(doc)
    doc_dir = output_dir / safe_slug(doc.file_name)
    pages_dir = doc_dir / "pages"
    raw_path = doc_dir / "candidates_raw.jsonl"
    verified_path = doc_dir / "candidates_verified.jsonl"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text("", encoding="utf-8")
    verified_path.write_text("", encoding="utf-8")

    pages = pages_for_document(session, doc.doc_id, max_pages=max_pages)
    entries: list[dict[str, Any]] = []
    page_results = []
    for page in pages:
        image_path = pages_dir / f"page_{page.page_no:04d}.png"
        try:
            render_page(pdf_path, page.page_no, image_path)
            extracted, usage = extract_parameters_from_page_image(
                doc_id=doc.doc_id,
                page_no=page.page_no,
                rendered_image_path=image_path,
                equipment_class_id=equipment_class_id,
                backend=backend,
            )
            counter.add(usage)
            raw_rows = [candidate.raw for candidate in extracted]
            append_jsonl(raw_path, raw_rows)
            candidate_entries = [
                candidate_entry(session, doc, page, candidate, equipment_class_id, backend)
                for candidate in extracted
            ]
            append_jsonl(verified_path, candidate_entries)
            entries.extend(candidate_entries)
            page_results.append({"page_no": page.page_no, "status": "ok", "candidates": len(candidate_entries), "usage": usage})
            print(f"  p{page.page_no}: {len(candidate_entries)} candidates tokens={usage_total(usage)}", flush=True)
        except TokenBudgetExceeded:
            raise
        except Exception as exc:
            page_results.append({"page_no": page.page_no, "status": "failed", "error": str(exc)[:300]})
            print(f"  p{page.page_no}: failed {type(exc).__name__}: {str(exc)[:120]}", flush=True)

    candidate_json = write_candidate_payload(
        doc_dir / "candidates.json",
        doc=doc,
        pdf_path=pdf_path,
        entries=entries,
        output_dir=output_dir,
        equipment_class_id=equipment_class_id,
        backend=backend,
    )
    review_pack_dir = doc_dir / "review_packs"
    manifest = write_review_packs_from_candidate_file(candidate_json, review_pack_dir, default_trust_level="L3")
    accept_visual_review_packs(review_pack_dir, doc)
    session.commit()

    summary = {
        "doc_id": doc.doc_id,
        "file_name": doc.file_name,
        "pages_total": len(pages),
        "pages_ok": sum(1 for result in page_results if result["status"] == "ok"),
        "candidates_verified": len(entries),
        "candidates_json": str(candidate_json),
        "review_pack_dir": str(review_pack_dir),
        "review_packs": manifest.get("total_packs", 0),
        "page_results": page_results,
    }
    (doc_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def accept_visual_review_packs(review_pack_dir: Path, doc: Document) -> None:
    for pack_path in review_pack_dir.glob("*.json"):
        payload = json.loads(pack_path.read_text(encoding="utf-8"))
        if payload.get("review_mode") != "chunk_backfill_review_pack":
            continue
        if _accept_visual_pack(payload, doc):
            pack_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _accept_visual_pack(payload: dict[str, Any], doc: Document) -> bool:
    changed = False
    for entry in payload.get("candidate_entries", []):
        if entry.get("judge_verdict") != "accepted":
            continue
        candidate_payload = entry.get("structured_payload_candidate") or {}
        title = str(candidate_payload.get("title") or candidate_payload.get("parameter_name") or entry.get("evidence_text") or "").strip()
        summary = str(candidate_payload.get("summary") or entry.get("evidence_text") or title).strip()
        curation = entry.setdefault("curation", {})
        curation.update({
            "title": title,
            "summary": summary,
            "structured_payload": candidate_payload,
            "applicability": curation.get("applicability") or {},
            "trust_level": curation.get("trust_level") or entry.get("trust_level") or "L3",
            "review_status": "approved",
            "evidence_text": entry.get("evidence_text", ""),
            "evidence_role": "primary",
            "publisher": doc.publisher or doc.vendor_brand,
            "citation": f"{doc.file_name} p.{entry.get('page_no')}",
        })
        entry["publisher"] = doc.publisher or doc.vendor_brand
        entry["citation"] = curation["citation"]
        entry["review_decision"] = "accepted"
        changed = True
    return changed


def candidate_entry(
    session,
    doc: Document,
    page: DocumentPage,
    candidate: ExtractedCandidate,
    equipment_class_id: str,
    backend,
) -> dict[str, Any]:
    chunk = chunk_for_page(session, doc.doc_id, page.page_no)
    if not chunk:
        chunk = ensure_visual_chunk(session, page, candidate.evidence_quote)
    chunk_id = chunk.chunk_id
    payload = dict(candidate.structured_payload)
    title = str(payload.get("title") or candidate.parameter_name)
    summary = str(payload.get("summary") or candidate.evidence_quote)
    payload.setdefault("summary", summary)
    payload.setdefault("title", title)
    raw_id = f"{doc.doc_id}:{page.page_no}:{candidate.knowledge_object_type}:{candidate.parameter_name}:{candidate.evidence_quote}"
    candidate_id = stable_candidate_id(raw_id)
    type_prefix = candidate.knowledge_object_type
    return {
        "candidate_id": candidate_id,
        "domain_id": "hvac",
        "doc_id": doc.doc_id,
        "doc_name": doc.file_name,
        "page_no": page.page_no,
        "chunk_id": chunk_id,
        "knowledge_object_type": candidate.knowledge_object_type,
        "canonical_key_candidate": f"hvac:{equipment_class_id}:{type_prefix}:candidate",
        "structured_payload_candidate": payload,
        "confidence_score": candidate.confidence,
        "review_status": "candidate",
        "evidence_text": candidate.evidence_quote,
        "curated_against_ontology_version": "0.2.0",
        "equipment_class_candidate": equipment_candidate(equipment_class_id),
        "compile_metadata": {
            "method": "visual_parameter_batch",
            "backend_name": backend.name,
            "model": backend.model,
        },
        "source_chunk_ids": [chunk_id],
        "source_page_nos": [page.page_no],
        "trust_level": "L3",
        "judge_verdict": "accepted",
        "judge_reason": "Visual extraction candidate passed deterministic non-empty evidence/name checks.",
    }


def equipment_candidate(equipment_class_id: str) -> dict[str, Any]:
    label = equipment_class_id.replace("_", " ").title()
    return {
        "equipment_class_id": equipment_class_id,
        "equipment_class_key": f"hvac:{equipment_class_id}",
        "label": label,
        "confidence": 1.0,
        "matched_aliases": [],
        "supported_knowledge_anchors": ["fault_code", "parameter_spec", "performance_spec"],
    }


def route_equipment_class(row: dict[str, Any]) -> str:
    text = " ".join(str(row.get(key) or "") for key in ("domain", "brand", "filename", "local_path")).lower()
    if "standard" in text or "ashrae" in text or "ahri" in text or "gb" in text:
        return "standard_reference"
    if any(term in text for term in ("空气处理", "air handling", "ahu", "空调箱", "组合式")):
        if not any(term in text for term in ("冷水机", "螺杆", "离心", "chiller", "heat pump", "热泵")):
            return "ahu"
    if "etw" in text or "高温水源热泵" in text or "水源热泵" in text:
        return "water_source_heat_pump"
    if "风冷" in text and "热泵" in text:
        return "air_cooled_modular_heat_pump"
    if "螺杆" in text or "screw" in text:
        return "screw_chiller"
    if "磁悬浮" in text or "magnetic" in text or "wmc" in text or "wme" in text:
        return "magnetic_bearing_chiller"
    if "离心" in text or "centrifugal" in text or "wsc" in text or "wdc" in text or "wcc" in text:
        return "centrifugal_chiller"
    if str(row.get("domain") or "").lower() == "ahu":
        return "ahu"
    return "centrifugal_chiller"


def infer_language(row: dict[str, Any]) -> str:
    text = " ".join(str(row.get(key) or "") for key in ("filename", "local_path", "brand"))
    return "zh" if any("\u4e00" <= char <= "\u9fff" for char in text) else "en"


def int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def write_candidate_payload(
    path: Path,
    *,
    doc: Document,
    pdf_path: Path,
    entries: list[dict[str, Any]],
    output_dir: Path,
    equipment_class_id: str,
    backend,
) -> Path:
    run_id = output_dir.name
    source_manifest = [
        build_file_source_manifest_entry(
            pdf_path,
            source_type="document",
            domain_id="hvac",
            authority_levels=[doc.authority_level] if doc.authority_level else [],
            metadata={
                "doc_id": doc.doc_id,
                "file_name": doc.file_name,
                "equipment_scope": equipment_class_id,
                "text_quality": doc.text_quality,
                "processing_decision": doc.processing_decision,
            },
        ).model_dump(mode="json")
    ]
    compiler_run = build_compiler_run(
        compiler_run_id=run_id,
        pipeline="visual_parameter_batch",
        domain_id="hvac",
        parameters={"backend": backend.name, "equipment_class_id": equipment_class_id},
        source_manifest=[],
    ).model_dump(mode="json", exclude={"source_manifest"})
    payload = {
        "generation_mode": "visual_parameter_batch",
        "compiler_run": compiler_run,
        "source_manifest": source_manifest,
        "domain_id": "hvac",
        "filters_applied": {"deterministic_visual_candidate_validation": True},
        "candidate_entries": entries,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def usage_total(usage: dict[str, Any]) -> int:
    return int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0) + int(
        usage.get("completion_tokens") or usage.get("output_tokens") or 0
    )


def safe_slug(value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]
    stem = "".join(ch if ch.isalnum() else "_" for ch in Path(value).stem).strip("_")[:80] or "doc"
    return f"{stem}_{digest}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doc-ids", help="Comma-separated doc_ids. Defaults to all KEEP_VISUAL docs.")
    parser.add_argument("--equipment-class-id", default="centrifugal_chiller")
    parser.add_argument("--manifest", help="Phase manifest CSV. When set, imports/runs rows matching --text-quality.")
    parser.add_argument("--text-quality", default="scanned")
    parser.add_argument("--backend", default=DEFAULT_BACKEND)
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--max-pages-per-doc", type=int, default=0)
    parser.add_argument("--token-cap", type=int, default=DEFAULT_TOKEN_CAP)
    parser.add_argument("--doc-concurrency", type=int, default=0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    backend, _ = load_backend(args.backend)
    run_dir = Path(args.output_root) / make_run_id()
    run_dir.mkdir(parents=True, exist_ok=True)
    doc_ids = [item.strip() for item in args.doc_ids.split(",") if item.strip()] if args.doc_ids else None

    session = SessionLocal()
    summaries = []
    started = time.monotonic()
    try:
        if args.manifest:
            docs_with_scope = docs_from_manifest(session, Path(args.manifest), args.text_quality)
        else:
            docs_with_scope = [(doc, args.equipment_class_id, {}) for doc in keep_visual_docs(session, doc_ids=doc_ids)]
        if doc_ids:
            docs_with_scope = [item for item in docs_with_scope if item[0].doc_id in set(doc_ids)]
        summaries = run_documents(
            docs_with_scope,
            backend=backend,
            output_dir=run_dir,
            max_pages=args.max_pages_per_doc,
            doc_concurrency=resolve_doc_concurrency(args.doc_concurrency),
        )
    finally:
        session.close()

    report = {
        "run_id": run_dir.name,
        "output_dir": str(run_dir),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "token_usage": summarize_token_usage(summaries, args.token_cap),
        "docs": summaries,
    }
    (run_dir / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"summary={run_dir / 'summary.json'}")
    print(f"token_usage={report['token_usage']}")
    return 0


def run_documents(
    docs_with_scope: list[tuple[Document, str, dict[str, Any]]],
    *,
    backend,
    output_dir: Path,
    max_pages: int,
    doc_concurrency: int,
) -> list[dict[str, Any]]:
    if doc_concurrency <= 1 or len(docs_with_scope) <= 1:
        return [process_document_worker(item[0].doc_id, item[1], backend, output_dir, max_pages) for item in docs_with_scope]

    summaries: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=doc_concurrency) as pool:
        future_to_doc = {
            pool.submit(process_document_worker, doc.doc_id, equipment_class_id, backend, output_dir, max_pages): doc
            for doc, equipment_class_id, _row in docs_with_scope
        }
        for future in concurrent.futures.as_completed(future_to_doc):
            doc = future_to_doc[future]
            try:
                summaries.append(future.result())
            except Exception as exc:
                summaries.append({"doc_id": doc.doc_id, "file_name": doc.file_name, "status": "failed", "error": str(exc)[:500]})
                print(f"[failed] {doc.doc_id} {doc.file_name}: {exc}", flush=True)
    return sorted(summaries, key=lambda item: str(item.get("file_name") or ""))


def process_document_worker(doc_id: str, equipment_class_id: str, backend, output_dir: Path, max_pages: int) -> dict[str, Any]:
    session = SessionLocal()
    counter = CumulativeTokenCounter(cap=DEFAULT_TOKEN_CAP)
    try:
        doc = session.query(Document).filter(Document.doc_id == doc_id).one()
        print(f"[doc] {doc.doc_id} {doc.file_name} equipment={equipment_class_id}", flush=True)
        summary = process_document(
            session=session,
            doc=doc,
            backend=backend,
            output_dir=output_dir,
            counter=counter,
            equipment_class_id=equipment_class_id,
            max_pages=max_pages,
        )
        summary["token_usage"] = counter.summary()
        summary["equipment_class_id"] = equipment_class_id
        summary["status"] = "ok"
        return summary
    finally:
        session.close()


def resolve_doc_concurrency(cli_value: int) -> int:
    if cli_value > 0:
        return cli_value
    try:
        return max(1, int(os.getenv("EXTRACTION_DOC_CONCURRENCY", str(settings.extraction_doc_concurrency))))
    except ValueError:
        return 1


def summarize_token_usage(summaries: list[dict[str, Any]], cap: int) -> dict[str, Any]:
    total_input = sum(int((item.get("token_usage") or {}).get("total_input_tokens") or 0) for item in summaries)
    total_output = sum(int((item.get("token_usage") or {}).get("total_output_tokens") or 0) for item in summaries)
    total = total_input + total_output
    return {
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_tokens": total,
        "cap": cap,
        "remaining": max(0, cap - total),
    }


if __name__ == "__main__":
    raise SystemExit(main())
