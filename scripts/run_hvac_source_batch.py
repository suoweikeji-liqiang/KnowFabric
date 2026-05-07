#!/usr/bin/env python3
"""Run a manifest-driven HVAC source batch without applying knowledge to production."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.chunking.service import ChunkingService  # noqa: E402
from packages.core.config import settings  # noqa: E402
from packages.db.models import ContentChunk, Document, DocumentPage  # noqa: E402
from packages.db.session import SessionLocal  # noqa: E402
from packages.ingest.service import IngestService  # noqa: E402
from packages.parser.service import ParserService  # noqa: E402
from packages.storage.manager import StorageManager  # noqa: E402
from scripts.prepare_review_pipeline_bundle import prepare_review_pipeline_bundle  # noqa: E402

BATCH_SUMMARY_JSON = "batch_summary.json"
BATCH_SUMMARY_MD = "BATCH_REPORT.md"


@dataclass(frozen=True)
class SourceItem:
    row_index: int
    path: Path
    batch_group: str
    priority: str
    brand: str
    authority_level: str
    document_kind: str
    equipment_scope: str
    page_count: str
    text_quality: str
    recommended_mode: str
    raw: dict[str, str]


def load_manifest(path: str | Path) -> list[SourceItem]:
    """Load a source inventory or starter batch manifest CSV."""

    rows = []
    with Path(path).open(encoding="utf-8", newline="") as handle:
        for index, row in enumerate(csv.DictReader(handle), start=1):
            source_path = Path(row.get("path") or "")
            rows.append(
                SourceItem(
                    row_index=index,
                    path=source_path,
                    batch_group=str(row.get("batch_group") or ""),
                    priority=str(row.get("extraction_priority") or ""),
                    brand=str(row.get("publisher_or_brand_guess") or "unknown"),
                    authority_level=str(row.get("authority_level_guess") or "unspecified"),
                    document_kind=str(row.get("document_kind_guess") or "unknown_document"),
                    equipment_scope=str(row.get("equipment_scope_guess") or "general_hvac"),
                    page_count=str(row.get("page_count") or ""),
                    text_quality=str(row.get("text_quality") or "unknown"),
                    recommended_mode=str(row.get("recommended_extraction_mode") or "unknown"),
                    raw={str(key): str(value) for key, value in row.items()},
                )
            )
    return rows


def select_items(
    items: list[SourceItem],
    *,
    groups: set[str],
    limit: int | None,
    include_ocr_holds: bool = False,
) -> list[SourceItem]:
    """Select manifest items for this run."""

    selected = [
        item
        for item in items
        if (not groups or item.batch_group in groups)
        and item.path.suffix.lower() == ".pdf"
        and (include_ocr_holds or item.recommended_mode != "ocr_or_multimodal_first")
    ]
    return selected[:limit] if limit is not None else selected


def make_run_id(prefix: str = "hvac_source_batch") -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"_{prefix}"


def slugify(value: str, *, max_length: int = 96) -> str:
    text = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "_", value).strip("_").lower()
    return (text or "source")[:max_length].strip("_") or "source"


def task_dir_for(output_dir: Path, item: SourceItem) -> Path:
    digest = hashlib.sha1(str(item.path).encode("utf-8")).hexdigest()[:10]
    return output_dir / f"{item.row_index:04d}_{slugify(item.path.stem)}_{digest}"


def planned_action(item: SourceItem) -> str:
    if item.batch_group == "A_standard_authority_first":
        if item.document_kind == "standard_guideline_control_sequences":
            return "standard_g36_section_context_extraction"
        return "standard_reference_chunk_prepare"
    if item.recommended_mode == "ocr_or_multimodal_first":
        return "hold_for_visual_pipeline"
    return "oem_text_review_bundle_prepare"


def build_task_plan(item: SourceItem, output_dir: Path) -> dict[str, Any]:
    return {
        "row_index": item.row_index,
        "path": str(item.path),
        "file_name": item.path.name,
        "batch_group": item.batch_group,
        "priority": item.priority,
        "brand": item.brand,
        "authority_level": item.authority_level,
        "document_kind": item.document_kind,
        "equipment_scope": item.equipment_scope,
        "page_count": item.page_count,
        "text_quality": item.text_quality,
        "recommended_mode": item.recommended_mode,
        "planned_action": planned_action(item),
        "task_dir": str(task_dir_for(output_dir, item)),
    }


def file_hash(storage: StorageManager, path: Path) -> str:
    return storage.calculate_file_hash(str(path))


def find_existing_doc(db, file_hash_value: str) -> Document | None:
    return db.query(Document).filter(Document.file_hash == file_hash_value).first()


def ensure_document_imported(item: SourceItem, *, storage: StorageManager) -> tuple[str, str]:
    """Import a PDF if needed and return (doc_id, import_status)."""

    db = SessionLocal()
    try:
        digest = file_hash(storage, item.path)
        existing = find_existing_doc(db, digest)
        if existing:
            if existing.source_domain != "hvac":
                existing.source_domain = "hvac"
                db.commit()
            return str(existing.doc_id), "existing"
        ingest = IngestService(storage)
        doc_id = ingest.import_document(db, str(item.path), source_domain="hvac", batch_id="hvac_source_batch")
        if not doc_id:
            existing = find_existing_doc(db, digest)
            if not existing:
                raise RuntimeError("document import returned duplicate but no existing document was found")
            return str(existing.doc_id), "existing"
        return str(doc_id), "imported"
    finally:
        db.close()


def count_pages_and_chunks(doc_id: str) -> tuple[int, int]:
    db = SessionLocal()
    try:
        pages = db.query(DocumentPage).filter(DocumentPage.doc_id == doc_id).count()
        chunks = db.query(ContentChunk).filter(ContentChunk.doc_id == doc_id).count()
        return int(pages), int(chunks)
    finally:
        db.close()


def ensure_parsed_and_chunked(doc_id: str, *, storage: StorageManager) -> dict[str, Any]:
    """Run parse/chunk only when records are missing."""

    pages_before, chunks_before = count_pages_and_chunks(doc_id)
    parse_result = {"status": "skipped_existing_pages", "pages_created": 0}
    chunk_result = {"status": "skipped_existing_chunks", "chunks_created": 0}
    if pages_before == 0:
        db = SessionLocal()
        try:
            parse_result = ParserService(storage).parse_document(db, doc_id)
        finally:
            db.close()
    pages_after_parse, chunks_after_parse = count_pages_and_chunks(doc_id)
    if chunks_after_parse == 0 and pages_after_parse > 0:
        db = SessionLocal()
        try:
            chunk_result = ChunkingService().chunk_document(db, doc_id)
        finally:
            db.close()
    pages_after, chunks_after = count_pages_and_chunks(doc_id)
    return {
        "pages_before": pages_before,
        "chunks_before": chunks_before,
        "pages_after": pages_after,
        "chunks_after": chunks_after,
        "parse_result": parse_result,
        "chunk_result": chunk_result,
    }


def maybe_prepare_review_bundle(args: argparse.Namespace, item: SourceItem, task_dir: Path, doc_id: str) -> dict[str, Any] | None:
    if not args.prepare_review_bundles:
        return None
    if planned_action(item) != "oem_text_review_bundle_prepare":
        return None
    bundle_dir = task_dir / "review_bundle"
    return prepare_review_pipeline_bundle(
        "hvac",
        bundle_dir,
        doc_id=doc_id,
        limit=args.candidate_limit,
        default_trust_level=args.default_trust_level,
        llm_backend_config_path=args.llm_backend_config,
        llm_backend_name=args.llm_backend_name,
        enable_llm=args.enable_llm,
        llm_enabled_types=tuple(args.llm_type or ()),
    )


def execute_task(args: argparse.Namespace, item: SourceItem, batch_dir: Path) -> dict[str, Any]:
    task_plan = build_task_plan(item, batch_dir / "tasks")
    task_dir = Path(task_plan["task_dir"])
    task_dir.mkdir(parents=True, exist_ok=False)
    (task_dir / "task_plan.json").write_text(json.dumps(task_plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not item.path.exists():
        return finish_task(task_dir, {**task_plan, "status": "failed", "error": "source file not found"})
    if not args.execute:
        return finish_task(task_dir, {**task_plan, "status": "planned"})

    storage = StorageManager(settings.storage_root)
    try:
        doc_id, import_status = ensure_document_imported(item, storage=storage)
        processing = ensure_parsed_and_chunked(doc_id, storage=storage)
        review_bundle = maybe_prepare_review_bundle(args, item, task_dir, doc_id)
        status = "prepared" if review_bundle else "chunked"
        if planned_action(item) == "hold_for_visual_pipeline":
            status = "held_for_visual_pipeline"
        return finish_task(
            task_dir,
            {
                **task_plan,
                "status": status,
                "doc_id": doc_id,
                "import_status": import_status,
                "processing": processing,
                "review_bundle": summarize_review_bundle(review_bundle),
            },
        )
    except Exception as exc:
        return finish_task(task_dir, {**task_plan, "status": "failed", "error": str(exc)})


def summarize_review_bundle(manifest: dict[str, Any] | None) -> dict[str, Any] | None:
    if not manifest:
        return None
    return {
        "prepare_manifest": manifest.get("paths", {}).get("prepare_manifest"),
        "candidate_entries": manifest.get("counts", {}).get("candidate_entries"),
        "review_packs": manifest.get("counts", {}).get("review_packs"),
        "ready_packs": manifest.get("counts", {}).get("ready_packs"),
        "compiler": manifest.get("compiler"),
        "health": manifest.get("health"),
    }


def finish_task(task_dir: Path, result: dict[str, Any]) -> dict[str, Any]:
    (task_dir / "task_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    return result


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# HVAC Source Batch Report",
        "",
        f"- Run ID: `{summary['run_id']}`",
        f"- Mode: `{'execute' if summary['execute'] else 'dry-run'}`",
        f"- Manifest: `{summary['manifest_path']}`",
        f"- Selected items: {summary['selected_count']}",
        f"- Output dir: `{summary['output_dir']}`",
        "",
        "## Status",
        "",
    ]
    for status, count in sorted(summary["status_counts"].items()):
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Groups", ""])
    for group, count in sorted(summary["group_counts"].items()):
        lines.append(f"- {group}: {count}")
    lines.extend(["", "## Tasks", "", "| # | Status | Group | Brand | Pages | Action | Path |", "|---:|---|---|---|---:|---|---|"])
    for item in summary["tasks"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(item["row_index"]),
                    str(item["status"]),
                    str(item["batch_group"]),
                    str(item["brand"]),
                    str(item["page_count"]),
                    str(item["planned_action"]),
                    str(item["path"]).replace("|", "/"),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def build_summary(args: argparse.Namespace, batch_dir: Path, tasks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "run_id": batch_dir.name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "execute": args.execute,
        "manifest_path": str(Path(args.manifest)),
        "output_dir": str(batch_dir),
        "selected_count": len(tasks),
        "status_counts": dict(counter(tasks, "status")),
        "group_counts": dict(counter(tasks, "batch_group")),
        "tasks": tasks,
    }


def counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "")
        counts[value] = counts.get(value, 0) + 1
    return counts


def write_batch_outputs(batch_dir: Path, summary: dict[str, Any]) -> None:
    (batch_dir / BATCH_SUMMARY_JSON).write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    (batch_dir / BATCH_SUMMARY_MD).write_text(render_report(summary) + "\n", encoding="utf-8")


def run_batch(args: argparse.Namespace) -> dict[str, Any]:
    items = load_manifest(args.manifest)
    groups = {item.strip() for item in args.groups.split(",") if item.strip()}
    selected = select_items(items, groups=groups, limit=args.limit, include_ocr_holds=args.include_ocr_holds)
    batch_dir = Path(args.output_dir) / make_run_id()
    batch_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(args.manifest, batch_dir / "input_manifest.csv")
    tasks = [execute_task(args, item, batch_dir) for item in selected]
    summary = build_summary(args, batch_dir, tasks)
    write_batch_outputs(batch_dir, summary)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="CSV from source inventory or starter batch manifest")
    parser.add_argument("--groups", default="A_standard_authority_first,B_oem_manual_text_first")
    parser.add_argument("--output-dir", default="output/hvac_source_batch")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--execute", action="store_true", help="Actually import/parse/chunk selected PDFs")
    parser.add_argument("--include-ocr-holds", action="store_true", help="Include rows marked for OCR/multimodal hold")
    parser.add_argument("--prepare-review-bundles", action="store_true", help="After chunking OEM manuals, build review bundles")
    parser.add_argument("--candidate-limit", type=int, default=100)
    parser.add_argument("--default-trust-level", default="L3")
    parser.add_argument("--enable-llm", action="store_true", help="Enable LLM-assisted chunk compiler for review bundles")
    parser.add_argument("--llm-backend-config")
    parser.add_argument("--llm-backend-name")
    parser.add_argument("--llm-type", action="append", dest="llm_type")
    return parser


def main(argv: list[str] | None = None) -> int:
    summary = run_batch(build_parser().parse_args(argv))
    print(
        f"batch status={summary['status_counts']} selected={summary['selected_count']} "
        f"report={Path(summary['output_dir']) / BATCH_SUMMARY_MD}"
    )
    return 1 if summary["status_counts"].get("failed") else 0


if __name__ == "__main__":
    raise SystemExit(main())
