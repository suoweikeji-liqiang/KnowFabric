#!/usr/bin/env python3
"""Orchestrate controlled HVAC authority-source extraction batches."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.core.config import settings  # noqa: E402
from packages.storage.manager import StorageManager  # noqa: E402
from scripts.run_hvac_source_batch import (  # noqa: E402
    SourceItem,
    ensure_document_imported,
    ensure_parsed_and_chunked,
    load_manifest,
    select_items,
    slugify,
)

G36_KIND = "standard_guideline_control_sequences"
STANDARD_GROUP = "A_standard_authority_first"
OEM_GROUP = "B_oem_manual_text_first"
VISUAL_GROUP = "C_ocr_multimodal_hold"


def make_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_hvac_authority_batch_pipeline"


def is_g36_item(item: SourceItem) -> bool:
    name = item.path.name.lower()
    return item.document_kind == G36_KIND or "guideline 36" in name or "高性能运行序列" in name


def plan_lanes(items: list[SourceItem], args: argparse.Namespace) -> dict[str, list[SourceItem]]:
    selected = select_items(items, groups={STANDARD_GROUP, OEM_GROUP}, limit=None)
    standards = [item for item in selected if item.batch_group == STANDARD_GROUP]
    oem = [item for item in selected if item.batch_group == OEM_GROUP][: args.oem_limit]
    visual = visual_items(items)[: args.visual_limit]
    return {
        "g36_standard": [item for item in standards if is_g36_item(item)][: args.standard_limit],
        "standard_reference_hold": [item for item in standards if not is_g36_item(item)][: args.standard_reference_limit],
        "oem_text": oem,
        "visual_queue": visual,
    }


def visual_items(items: list[SourceItem]) -> list[SourceItem]:
    return [
        item
        for item in select_items(items, groups={VISUAL_GROUP}, limit=None, include_ocr_holds=True)
        if item.recommended_mode == "ocr_or_multimodal_first" or item.text_quality == "low_or_no_text"
    ]


def ensure_doc_ready(item: SourceItem) -> dict[str, Any]:
    storage = StorageManager(settings.storage_root)
    doc_id, import_status = ensure_document_imported(item, storage=storage)
    processing = ensure_parsed_and_chunked(doc_id, storage=storage)
    return {"doc_id": doc_id, "import_status": import_status, "processing": processing}


def g36_command(args: argparse.Namespace, doc_id: str) -> list[str]:
    return [
        sys.executable,
        "scripts/run_ashrae_g36_parallel_sections.py",
        "--doc-id",
        doc_id,
        "--sections",
        args.g36_sections,
        "--extract-backend",
        args.extract_backend,
        "--judge-backend",
        args.judge_backend,
        "--extract-output-dir",
        str(Path(args.output_dir) / "ashrae_guideline36_parallel_fullbook"),
        "--workspace-root",
        str(Path(args.output_dir) / "ashrae_g36_parallel_sections"),
        "--workers",
        str(args.g36_workers),
        "--budget-rmb-per-section",
        str(args.budget_rmb_per_section),
        "--target-candidates-per-section",
        str(args.g36_target_candidates),
        "--input-mode",
        args.g36_input_mode,
        "--context-sections",
        args.g36_context_sections,
    ]


def oem_command(args: argparse.Namespace, output_dir: Path) -> list[str]:
    return [
        sys.executable,
        "scripts/run_hvac_doclevel_extraction_batch.py",
        "--manifest",
        args.manifest,
        "--groups",
        OEM_GROUP,
        "--output-dir",
        str(output_dir / "hvac_doclevel_extraction_batch"),
        "--limit",
        str(args.oem_limit),
        "--execute",
        "--backends",
        args.extract_backend,
        "--judge-backend",
        args.judge_backend,
        "--target-candidates",
        str(args.oem_target_candidates),
        "--backend-timeout-seconds",
        str(args.backend_timeout_seconds),
    ]


def run_command(command: list[str], log_dir: Path, name: str, execute: bool) -> dict[str, Any]:
    log_dir.mkdir(parents=True, exist_ok=True)
    result = {"name": name, "command": command, "status": "planned"}
    if not execute:
        return result
    started = time.monotonic()
    completed = subprocess.run(command, text=True, capture_output=True)
    (log_dir / f"{name}.stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (log_dir / f"{name}.stderr.txt").write_text(completed.stderr, encoding="utf-8")
    result.update(
        {
            "status": "passed" if completed.returncode == 0 else "failed",
            "returncode": completed.returncode,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "stdout_tail": completed.stdout[-2000:],
            "stderr_tail": completed.stderr[-2000:],
        }
    )
    return result


def write_visual_queue(path: Path, items: list[SourceItem]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["row_index", "path", "brand", "document_kind", "page_count", "text_quality", "recommended_mode"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in items:
            writer.writerow({field: getattr(item, field, "") for field in fields})


def item_summary(item: SourceItem) -> dict[str, Any]:
    return {
        "row_index": item.row_index,
        "file_name": item.path.name,
        "path": str(item.path),
        "batch_group": item.batch_group,
        "brand": item.brand,
        "document_kind": item.document_kind,
        "page_count": item.page_count,
        "text_quality": item.text_quality,
        "recommended_mode": item.recommended_mode,
    }


def run_pipeline(args: argparse.Namespace) -> dict[str, Any]:
    items = load_manifest(args.manifest)
    lanes = plan_lanes(items, args)
    run_dir = Path(args.output_dir) / make_run_id()
    run_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(args.manifest, run_dir / "input_manifest.csv")
    results = build_initial_results(lanes, run_dir, args)
    write_outputs(run_dir, args, lanes, results)
    return build_summary(run_dir, args, lanes, results)


def build_initial_results(lanes: dict[str, list[SourceItem]], run_dir: Path, args: argparse.Namespace) -> list[dict[str, Any]]:
    results = []
    for item in lanes["g36_standard"]:
        results.append(run_g36_lane(args, item, run_dir))
    if lanes["oem_text"]:
        results.append(run_command(oem_command(args, run_dir), run_dir / "logs", "oem_text_doclevel", args.execute))
    write_visual_queue(run_dir / "visual_queue.csv", lanes["visual_queue"])
    return results


def run_g36_lane(args: argparse.Namespace, item: SourceItem, run_dir: Path) -> dict[str, Any]:
    name = f"g36_{item.row_index:04d}_{slugify(item.path.stem, max_length=40)}"
    ready = resolve_g36_doc(args, item)
    result = run_command(g36_command(args, ready["doc_id"]), run_dir / "logs", name, args.execute)
    result.update({"source_item": item_summary(item), "doc_ready": ready})
    return result


def resolve_g36_doc(args: argparse.Namespace, item: SourceItem) -> dict[str, Any]:
    if args.g36_doc_id:
        return {"doc_id": args.g36_doc_id, "import_status": "provided_by_cli"}
    if args.execute:
        return ensure_doc_ready(item)
    return {"doc_id": "<resolved-on-execute>"}


def build_summary(run_dir: Path, args: argparse.Namespace, lanes: dict[str, list[SourceItem]], results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "run_id": run_dir.name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "execute": args.execute,
        "manifest": args.manifest,
        "output_dir": str(run_dir),
        "lane_counts": {name: len(items) for name, items in lanes.items()},
        "lanes": {name: [item_summary(item) for item in items] for name, items in lanes.items()},
        "results": results,
    }


def write_outputs(run_dir: Path, args: argparse.Namespace, lanes: dict[str, list[SourceItem]], results: list[dict[str, Any]]) -> None:
    summary = build_summary(run_dir, args, lanes, results)
    (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    (run_dir / "REPORT.md").write_text(render_report(summary) + "\n", encoding="utf-8")


def render_report(summary: dict[str, Any]) -> str:
    lines = report_header(summary)
    lines.extend(report_lanes(summary))
    lines.extend(report_results(summary))
    lines.extend(report_next_actions(summary))
    return "\n".join(lines)


def report_header(summary: dict[str, Any]) -> list[str]:
    return [
        "# HVAC Authority Batch Pipeline Report",
        "",
        f"- Run ID: `{summary['run_id']}`",
        f"- Mode: `{'execute' if summary['execute'] else 'dry-run'}`",
        f"- Manifest: `{summary['manifest']}`",
        f"- Output dir: `{summary['output_dir']}`",
        "",
    ]


def report_lanes(summary: dict[str, Any]) -> list[str]:
    lines = ["## Lane Counts", ""]
    for name, count in summary["lane_counts"].items():
        lines.append(f"- {name}: {count}")
    return lines + [""]


def report_results(summary: dict[str, Any]) -> list[str]:
    lines = ["## Executed Commands", "", "| Name | Status | Seconds |", "|---|---|---:|"]
    for result in summary["results"]:
        lines.append(f"| `{result['name']}` | {result['status']} | {result.get('elapsed_seconds', '-')} |")
    return lines + [""]


def report_next_actions(summary: dict[str, Any]) -> list[str]:
    return [
        "## Notes",
        "",
        "- `g36_standard` uses the existing ASHRAE G36 section-context extraction runner.",
        "- `oem_text` uses document-level extraction plus model review.",
        "- `standard_reference_hold` is intentionally held until a standard-specific extractor is selected.",
        "- `visual_queue.csv` lists low-text/image-heavy PDFs for visual semantic validation.",
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", default="output/hvac_authority_batch_pipeline")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--extract-backend", default="deepseek-v4-pro")
    parser.add_argument("--judge-backend", default="deepseek-v4-pro-judge")
    parser.add_argument("--oem-limit", type=int, default=5)
    parser.add_argument("--oem-target-candidates", type=int, default=60)
    parser.add_argument("--standard-limit", type=int, default=1)
    parser.add_argument("--standard-reference-limit", type=int, default=20)
    parser.add_argument("--visual-limit", type=int, default=20)
    parser.add_argument("--g36-doc-id", default="")
    parser.add_argument("--g36-sections", default="all")
    parser.add_argument("--g36-workers", type=int, default=2)
    parser.add_argument("--g36-target-candidates", type=int, default=40)
    parser.add_argument("--g36-input-mode", choices=["full_book", "section_context"], default="section_context")
    parser.add_argument("--g36-context-sections", default="3,5.1")
    parser.add_argument("--budget-rmb-per-section", type=float, default=10.0)
    parser.add_argument("--backend-timeout-seconds", type=int, default=1500)
    return parser


def main(argv: list[str] | None = None) -> int:
    summary = run_pipeline(build_parser().parse_args(argv))
    print(f"authority_batch status={result_counts(summary)} report={Path(summary['output_dir']) / 'REPORT.md'}")
    return 1 if result_counts(summary).get("failed") else 0


def result_counts(summary: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for result in summary["results"]:
        status = str(result.get("status"))
        counts[status] = counts.get(status, 0) + 1
    return counts


if __name__ == "__main__":
    raise SystemExit(main())
