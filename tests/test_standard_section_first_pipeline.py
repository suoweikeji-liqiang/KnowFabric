from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_script_module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


plan_matrix = load_script_module("plan_section_target_matrix", "scripts/plan_section_target_matrix.py")
prepare_subset = load_script_module("prepare_standard_subset_from_matrix", "scripts/prepare_standard_subset_from_matrix.py")


def test_page_heading_segmentation_keeps_contiguous_section_pages_together():
    pages = [
        plan_matrix.PageRecord(1, "1.1CHAPTER 1\nCENTRAL COOLING AND HEATING PLANTS\nintro text", 2, ["a", "b"]),
        plan_matrix.PageRecord(2, "Central Cooling and Heating Plants 1.2\nbody text", 2, ["c", "d"]),
        plan_matrix.PageRecord(3, "Central Cooling and Heating Plants 1.3\nmore body", 1, ["e"]),
        plan_matrix.PageRecord(4, "2.1CHAPTER 2\nAIR HANDLING AND DISTRIBUTION\nintro text", 2, ["f", "g"]),
    ]

    sections = plan_matrix.build_sections_from_page_headings(pages)

    assert [(item.section_title, item.page_start, item.page_end) for item in sections] == [
        ("CENTRAL COOLING AND HEATING PLANTS", 1, 3),
        ("AIR HANDLING AND DISTRIBUTION", 4, 4),
    ]


def test_select_sections_respects_section_spans_and_scores():
    sections = [
        prepare_subset.MatrixSection(
            section_title="Central Cooling and Heating Plants",
            page_start=30,
            page_end=36,
            chunk_count=24,
            candidate_knowledge_types=("application_guidance", "operational_sequence"),
            confidence="high",
            sample_text="design should control sequence and application guidance for chillers",
            section_source="page_heading",
        ),
        prepare_subset.MatrixSection(
            section_title="Bibliography",
            page_start=37,
            page_end=37,
            chunk_count=1,
            candidate_knowledge_types=("application_guidance",),
            confidence="low",
            sample_text="references only",
            section_source="page_heading",
        ),
        prepare_subset.MatrixSection(
            section_title="Planning the Audit",
            page_start=5,
            page_end=6,
            chunk_count=2,
            candidate_knowledge_types=("application_guidance",),
            confidence="high",
            sample_text="audit planning should define scope and objectives",
            section_source="pdf_outline",
        ),
    ]

    selected = prepare_subset.select_sections(
        sections,
        knowledge_types={"application_guidance", "operational_sequence"},
        min_confidence="high",
        max_sections=2,
        max_pages=12,
    )

    assert [(item.section_title, item.page_start, item.page_end) for item in selected] == [
        ("Planning the Audit", 5, 6),
        ("Central Cooling and Heating Plants", 30, 36),
    ]
