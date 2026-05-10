#!/usr/bin/env python3
"""Select high-value sections from a standard section matrix and build a subset PDF + manifest."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypdf import PdfWriter


@dataclass(frozen=True)
class MatrixSection:
    section_title: str
    page_start: int
    page_end: int
    chunk_count: int
    candidate_knowledge_types: tuple[str, ...]
    confidence: str
    sample_text: str
    section_source: str = "unknown"
    llm_section_topic: str = ""
    llm_knowledge_goal: str = ""
    llm_allowed_knowledge_types: tuple[str, ...] = ()
    llm_equipment_anchor: str = ""
    llm_should_extract: bool | None = None
    llm_route_confidence: str = ""
    llm_route_reason: str = ""


NEGATIVE_TITLE_PATTERNS = (
    "contents",
    "contributors",
    "preface",
    "index",
    "references",
    "isbn",
    "technical committees",
    "research",
)

NEGATIVE_SAMPLE_PATTERNS = (
    "contents",
    "contributors",
    "preface",
    "index",
    "isbn",
    "copyright",
    "technical committees",
    "references",
)

POSITIVE_EVIDENCE_PATTERNS = (
    "shall",
    "should",
    "must",
    "require",
    "required",
    "ensure",
    "consider",
    "recommended",
    "select",
    "selection",
    "procedure",
    "steps",
    "design",
    "application",
    "operat",
    "control",
    "sequence",
    "setpoint",
    "parameter",
    "limit",
    "threshold",
    "flow",
    "temperature",
    "pressure",
    "ventilation",
    "commissioning",
    "maintenance",
)


def load_matrix(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def parse_sections(payload: dict[str, Any]) -> list[MatrixSection]:
    sections = []
    for row in payload.get("sections", []):
        sections.append(
            MatrixSection(
                section_title=str(row.get("section_title") or "untitled"),
                page_start=int(row["page_start"]),
                page_end=int(row["page_end"]),
                chunk_count=int(row["chunk_count"]),
                candidate_knowledge_types=tuple(str(item) for item in row.get("candidate_knowledge_types", [])),
                confidence=str(row.get("confidence") or "none"),
                sample_text=str(row.get("sample_text") or ""),
                section_source=str(row.get("section_source") or "unknown"),
                llm_section_topic=str(row.get("llm_section_topic") or ""),
                llm_knowledge_goal=str(row.get("llm_knowledge_goal") or ""),
                llm_allowed_knowledge_types=tuple(str(item) for item in row.get("llm_allowed_knowledge_types", [])),
                llm_equipment_anchor=str(row.get("llm_equipment_anchor") or ""),
                llm_should_extract=row.get("llm_should_extract"),
                llm_route_confidence=str(row.get("llm_route_confidence") or ""),
                llm_route_reason=str(row.get("llm_route_reason") or ""),
            )
        )
    return sections


def confidence_rank(value: str) -> int:
    return {"none": 0, "low": 1, "medium": 2, "high": 3}.get(value, 0)


def negative_section_penalty(section: MatrixSection) -> int:
    title = section.section_title.lower()
    sample = section.sample_text.lower()
    penalty = 0
    if any(token in title for token in NEGATIVE_TITLE_PATTERNS):
        penalty += 6
    if any(token in sample for token in NEGATIVE_SAMPLE_PATTERNS):
        penalty += 4
    if title.startswith("chapter ") or "chapter" in title and len(section.sample_text) < 120:
        penalty += 2
    return penalty


def positive_signal_score(section: MatrixSection, knowledge_types: set[str]) -> int:
    title = section.section_title.lower()
    sample = section.sample_text.lower()
    score = 0
    type_matches = knowledge_types & set(section.candidate_knowledge_types)
    score += len(type_matches) * 3
    score += confidence_rank(section.confidence) * 2
    score += sum(1 for token in POSITIVE_EVIDENCE_PATTERNS if token in sample) // 2
    if "application_guidance" in type_matches:
        score += 2
    if "parameter_spec" in type_matches:
        score += 1
    if "operational_sequence" in type_matches:
        score += 1
    if any(token in title for token in ("design process", "planning", "conducting", "application", "selection", "guidance")):
        score += 3
    if section.section_source == "pdf_outline":
        score += 2
    page_span = section.page_end - section.page_start + 1
    if page_span >= 2:
        score += min(page_span, 4)
    return score


def section_score(section: MatrixSection, knowledge_types: set[str]) -> int:
    score = positive_signal_score(section, knowledge_types) - negative_section_penalty(section)
    if section.llm_should_extract is False:
        score -= 20
    if section.llm_should_extract is True:
        score += 6
    llm_allowed = set(section.llm_allowed_knowledge_types)
    if llm_allowed and knowledge_types & llm_allowed:
        score += 4
    elif llm_allowed and knowledge_types and not (knowledge_types & llm_allowed):
        score -= 8
    if section.llm_route_confidence == "high":
        score += 2
    elif section.llm_route_confidence == "low":
        score -= 1
    return score


def select_sections(
    sections: list[MatrixSection],
    *,
    knowledge_types: set[str],
    min_confidence: str,
    max_sections: int,
    max_pages: int,
) -> list[MatrixSection]:
    selected: list[MatrixSection] = []
    selected_pages = 0
    floor = confidence_rank(min_confidence)
    ranked = sorted(
        sections,
        key=lambda section: (
            -section_score(section, knowledge_types),
            -confidence_rank(section.confidence),
            section.page_start,
        ),
    )
    for section in ranked:
        if confidence_rank(section.confidence) < floor:
            continue
        llm_allowed = set(section.llm_allowed_knowledge_types)
        if llm_allowed:
            if knowledge_types and not (knowledge_types & llm_allowed):
                continue
        elif knowledge_types and not (knowledge_types & set(section.candidate_knowledge_types)):
            continue
        if section_score(section, knowledge_types) <= 0:
            continue
        page_span = section.page_end - section.page_start + 1
        if len(selected) >= max_sections:
            break
        if selected_pages + page_span > max_pages:
            continue
        selected.append(section)
        selected_pages += page_span
    return sorted(selected, key=lambda section: (section.page_start, section.page_end))


def expand_pages(sections: list[MatrixSection]) -> list[int]:
    pages: set[int] = set()
    for section in sections:
        for page in range(section.page_start, section.page_end + 1):
            pages.add(page)
    return sorted(pages)


def write_subset_pdf(source_pdf: Path, pages: list[int], output_pdf: Path) -> None:
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    # pypdf append uses zero-based inclusive/exclusive ranges or explicit page lists
    writer.append(str(source_pdf), pages=[page - 1 for page in pages], import_outline=False, excluded_fields=["/B"])
    with output_pdf.open("wb") as handle:
        writer.write(handle)


def write_manifest(output_path: Path, source_pdf: Path, pages: list[int]) -> None:
    write_manifest_with_equipment_scope(output_path, source_pdf, pages, "general_hvac")


def write_manifest_with_equipment_scope(
    output_path: Path,
    source_pdf: Path,
    pages: list[int],
    equipment_scope_id: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "batch_group",
        "batch_reason",
        "extraction_priority",
        "publisher_or_brand_guess",
        "authority_level_guess",
        "document_kind_guess",
        "equipment_scope_guess",
        "page_count",
        "text_quality",
        "recommended_extraction_mode",
        "size_mb",
        "path",
    ]
    row = {
        "batch_group": "A_standard_authority_first",
        "batch_reason": "section-first standard subset generated from section matrix",
        "extraction_priority": "P0_standard_subset_trial",
        "publisher_or_brand_guess": "ASHRAE",
        "authority_level_guess": "industry_standard_or_reference",
        "document_kind_guess": "standard_handbook_subset",
        "equipment_scope_guess": equipment_scope_id,
        "page_count": str(len(pages)),
        "text_quality": "good_text",
        "recommended_extraction_mode": "section_first_subset",
        "size_mb": "",
        "path": str(source_pdf),
    }
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(row)


def write_selection_report(
    output_dir: Path,
    *,
    doc_id: str,
    doc_name: str,
    source_pdf: Path,
    selected_sections: list[MatrixSection],
    pages: list[int],
    subset_pdf: Path,
    manifest_path: Path,
    knowledge_types: list[str],
    min_confidence: str,
    equipment_scope_id: str,
) -> None:
    payload = {
        "doc_id": doc_id,
        "doc_name": doc_name,
        "source_pdf": str(source_pdf),
        "selected_pages": pages,
        "selected_page_count": len(pages),
        "knowledge_types_filter": knowledge_types,
        "min_confidence": min_confidence,
        "equipment_scope_id": equipment_scope_id,
        "subset_pdf": str(subset_pdf),
        "manifest_path": str(manifest_path),
        "sections": [
            {
                "section_title": item.section_title,
                "page_start": item.page_start,
                "page_end": item.page_end,
                "chunk_count": item.chunk_count,
                "candidate_knowledge_types": list(item.candidate_knowledge_types),
                "confidence": item.confidence,
                "sample_text": item.sample_text,
                "section_source": item.section_source,
                "score": section_score(item, set(knowledge_types)),
            }
            for item in selected_sections
        ],
    }
    (output_dir / "selected_sections.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Standard Subset Selection",
        "",
        f"- Document: `{doc_name}`",
        f"- Doc ID: `{doc_id}`",
        f"- Source PDF: `{source_pdf}`",
        f"- Knowledge types filter: `{', '.join(knowledge_types)}`",
        f"- Minimum confidence: `{min_confidence}`",
        f"- Equipment scope override: `{equipment_scope_id}`",
        f"- Selection mode: `section_first`",
        f"- Selected pages: `{','.join(str(page) for page in pages)}`",
        f"- Subset PDF: `{subset_pdf}`",
        f"- Manifest: `{manifest_path}`",
        "",
        "| Section | Pages | Types | Confidence | Score | Sample |",
        "|---|---:|---|---|---:|---|",
    ]
    for item in selected_sections:
        lines.append(
            f"| {item.section_title[:90]} | {item.page_start}-{item.page_end} | "
            f"{', '.join(item.candidate_knowledge_types) or '-'} | {item.confidence} | "
            f"{section_score(item, set(knowledge_types))} | {item.sample_text[:140].replace('|', '/')} |"
        )
    (output_dir / "SELECTED_SECTIONS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix-json", type=Path, required=True)
    parser.add_argument("--source-pdf", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--knowledge-types",
        default="application_guidance,parameter_spec,operational_sequence",
        help="Comma-separated target knowledge types to prioritize",
    )
    parser.add_argument("--min-confidence", default="high", choices=["high", "medium", "low", "none"])
    parser.add_argument("--max-sections", type=int, default=8)
    parser.add_argument("--max-pages", type=int, default=8)
    parser.add_argument("--subset-name", default="")
    parser.add_argument("--equipment-scope-id", default="general_hvac")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    payload = load_matrix(args.matrix_json)
    sections = parse_sections(payload)
    knowledge_types = [item.strip() for item in args.knowledge_types.split(",") if item.strip()]
    selected = select_sections(
        sections,
        knowledge_types=set(knowledge_types),
        min_confidence=args.min_confidence,
        max_sections=args.max_sections,
        max_pages=args.max_pages,
    )
    if not selected:
        raise SystemExit("No sections matched the requested filters")

    pages = expand_pages(selected)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = args.subset_name or f"{payload['doc_id']}_subset_pages_{'_'.join(str(page) for page in pages)}"
    subset_pdf = output_dir / f"{stem}.pdf"
    manifest_path = output_dir / "manifest.csv"
    write_subset_pdf(args.source_pdf, pages, subset_pdf)
    write_manifest_with_equipment_scope(manifest_path, subset_pdf, pages, args.equipment_scope_id)
    write_selection_report(
        output_dir,
        doc_id=str(payload["doc_id"]),
        doc_name=str(payload["doc_name"]),
        source_pdf=args.source_pdf,
        selected_sections=selected,
        pages=pages,
        subset_pdf=subset_pdf,
        manifest_path=manifest_path,
        knowledge_types=knowledge_types,
        min_confidence=args.min_confidence,
        equipment_scope_id=args.equipment_scope_id,
    )
    print(output_dir / "SELECTED_SECTIONS.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
