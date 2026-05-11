"""Tests for the HVAC authority batch pipeline orchestrator."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.run_hvac_authority_batch_pipeline import build_parser, is_g36_item, plan_lanes, run_pipeline
from scripts.run_hvac_source_batch import load_manifest


def test_plan_lanes_routes_authority_sources(tmp_path: Path) -> None:
    items = load_manifest(write_manifest(tmp_path))
    args = build_parser().parse_args(["--manifest", str(tmp_path / "manifest.csv"), "--oem-limit", "1"])

    lanes = plan_lanes(items, args)

    assert [item.path.name for item in lanes["g36_standard"]] == ["HVAC系统高性能运行序列指南.pdf"]
    assert [item.path.name for item in lanes["standard_reference_hold"]] == ["ASHRAE手册2024.pdf"]
    assert [item.path.name for item in lanes["oem_text"]] == ["trane_manual.pdf"]
    assert [item.path.name for item in lanes["oem_fault_reference_hold"]] == ["fault_code_manual.pdf"]
    assert [item.path.name for item in lanes["visual_queue"]] == ["scan_manual.pdf"]
    assert is_g36_item(lanes["g36_standard"][0])


def test_run_pipeline_dry_run_writes_report_and_visual_queue(tmp_path: Path) -> None:
    manifest = write_manifest(tmp_path)
    output_dir = tmp_path / "out"
    args = build_parser().parse_args(
        [
            "--manifest",
            str(manifest),
            "--output-dir",
            str(output_dir),
            "--oem-limit",
            "1",
            "--visual-limit",
            "1",
        ]
    )

    summary = run_pipeline(args)

    run_dir = Path(summary["output_dir"])
    assert summary["execute"] is False
    assert summary["lane_counts"] == {
        "g36_standard": 1,
        "standard_reference_hold": 1,
        "oem_text": 1,
        "oem_fault_reference_hold": 1,
        "visual_queue": 1,
    }
    assert (run_dir / "REPORT.md").exists()
    assert (run_dir / "visual_queue.csv").exists()
    saved = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert saved["results"][0]["status"] == "planned"
    assert "run_ashrae_g36_parallel_sections.py" in " ".join(saved["results"][0]["command"])


def test_plan_lanes_supports_oem_offset(tmp_path: Path) -> None:
    items = load_manifest(write_manifest(tmp_path))
    args = build_parser().parse_args(["--manifest", str(tmp_path / "manifest.csv"), "--oem-offset", "1", "--oem-limit", "1"])

    lanes = plan_lanes(items, args)

    assert [item.path.name for item in lanes["oem_text"]] == ["carrier_manual.pdf"]


def write_manifest(tmp_path: Path) -> Path:
    rows = [
        row(tmp_path, "A_standard_authority_first", "ASHRAE", "standard_guideline_control_sequences", "good_text", "section_context_or_chapter_batch", "HVAC系统高性能运行序列指南.pdf"),
        row(tmp_path, "A_standard_authority_first", "ASHRAE", "standard_handbook", "good_text", "doc_level_or_section_context", "ASHRAE手册2024.pdf"),
        row(tmp_path, "B_oem_manual_text_first", "Trane", "fault_code_reference", "good_text", "doc_level_single_call", "fault_code_manual.pdf"),
        row(tmp_path, "B_oem_manual_text_first", "Trane", "operation_manual", "good_text", "doc_level_single_call", "trane_manual.pdf"),
        row(tmp_path, "B_oem_manual_text_first", "Carrier", "operation_manual", "good_text", "doc_level_single_call", "carrier_manual.pdf"),
        row(tmp_path, "C_ocr_multimodal_hold", "Carrier", "technical_manual", "low_or_no_text", "ocr_or_multimodal_first", "scan_manual.pdf"),
    ]
    for item in rows:
        Path(item["path"]).write_text("placeholder", encoding="utf-8")
    path = tmp_path / "manifest.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


def row(tmp_path: Path, group: str, brand: str, kind: str, quality: str, mode: str, filename: str) -> dict[str, str]:
    return {
        "batch_group": group,
        "extraction_priority": "P0",
        "publisher_or_brand_guess": brand,
        "authority_level_guess": "industry_standard_or_reference" if group.startswith("A_") else "oem_manual_or_vendor_doc",
        "document_kind_guess": kind,
        "equipment_scope_guess": "general_hvac",
        "page_count": "10",
        "text_quality": quality,
        "recommended_extraction_mode": mode,
        "path": str(tmp_path / filename),
    }
