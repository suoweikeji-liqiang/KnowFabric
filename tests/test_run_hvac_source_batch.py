"""Tests for the HVAC source batch runner."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.run_hvac_source_batch import (  # noqa: E402
    BATCH_SUMMARY_JSON,
    build_parser,
    load_manifest,
    planned_action,
    run_batch,
    select_items,
)


def test_load_manifest_reads_starter_batch_rows(tmp_path: Path) -> None:
    manifest = write_manifest(tmp_path)

    items = load_manifest(manifest)

    assert len(items) == 3
    assert items[0].batch_group == "A_standard_authority_first"
    assert items[1].brand == "Trane"
    assert items[2].recommended_mode == "ocr_or_multimodal_first"


def test_select_items_filters_groups_and_skips_ocr_holds(tmp_path: Path) -> None:
    items = load_manifest(write_manifest(tmp_path))

    selected = select_items(
        items,
        groups={"A_standard_authority_first", "B_oem_manual_text_first", "C_ocr_multimodal_hold"},
        limit=None,
    )

    assert [item.batch_group for item in selected] == ["A_standard_authority_first", "B_oem_manual_text_first"]


def test_select_items_can_include_ocr_holds(tmp_path: Path) -> None:
    items = load_manifest(write_manifest(tmp_path))

    selected = select_items(items, groups={"C_ocr_multimodal_hold"}, limit=None, include_ocr_holds=True)

    assert len(selected) == 1
    assert planned_action(selected[0]) == "hold_for_visual_pipeline"


def test_run_batch_dry_run_writes_per_task_outputs(tmp_path: Path) -> None:
    manifest = write_manifest(tmp_path)
    output_dir = tmp_path / "out"
    args = build_parser().parse_args(
        [
            "--manifest",
            str(manifest),
            "--groups",
            "A_standard_authority_first,B_oem_manual_text_first",
            "--output-dir",
            str(output_dir),
            "--limit",
            "2",
        ]
    )

    summary = run_batch(args)

    batch_dir = Path(summary["output_dir"])
    assert summary["status_counts"] == {"planned": 2}
    assert (batch_dir / BATCH_SUMMARY_JSON).exists()
    assert (batch_dir / "BATCH_REPORT.md").exists()
    task_results = sorted((batch_dir / "tasks").glob("*/task_result.json"))
    assert len(task_results) == 2
    first_task = json.loads(task_results[0].read_text(encoding="utf-8"))
    assert first_task["status"] == "planned"
    assert first_task["planned_action"] == "standard_g36_section_context_extraction"


def write_manifest(tmp_path: Path) -> Path:
    pdf_a = tmp_path / "HVAC系统高性能运行序列指南.pdf"
    pdf_b = tmp_path / "trane_manual.pdf"
    pdf_c = tmp_path / "scan_manual.pdf"
    for path in [pdf_a, pdf_b, pdf_c]:
        path.write_text("placeholder", encoding="utf-8")
    rows = [
        {
            "batch_group": "A_standard_authority_first",
            "extraction_priority": "P0_run_first",
            "publisher_or_brand_guess": "ASHRAE",
            "authority_level_guess": "industry_standard_or_reference",
            "document_kind_guess": "standard_guideline_control_sequences",
            "equipment_scope_guess": "general_hvac",
            "page_count": "292",
            "text_quality": "good_text",
            "recommended_extraction_mode": "section_context_or_chapter_batch",
            "path": str(pdf_a),
        },
        {
            "batch_group": "B_oem_manual_text_first",
            "extraction_priority": "P1_batch_extract",
            "publisher_or_brand_guess": "Trane",
            "authority_level_guess": "oem_manual_or_vendor_doc",
            "document_kind_guess": "operation_installation_manual",
            "equipment_scope_guess": "screw_chiller",
            "page_count": "32",
            "text_quality": "good_text",
            "recommended_extraction_mode": "doc_level_single_call",
            "path": str(pdf_b),
        },
        {
            "batch_group": "C_ocr_multimodal_hold",
            "extraction_priority": "P2_needs_ocr_or_visual_check",
            "publisher_or_brand_guess": "Carrier",
            "authority_level_guess": "oem_manual_or_vendor_doc",
            "document_kind_guess": "technical_manual",
            "equipment_scope_guess": "centrifugal_chiller",
            "page_count": "97",
            "text_quality": "low_or_no_text",
            "recommended_extraction_mode": "ocr_or_multimodal_first",
            "path": str(pdf_c),
        },
    ]
    path = tmp_path / "manifest.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path
