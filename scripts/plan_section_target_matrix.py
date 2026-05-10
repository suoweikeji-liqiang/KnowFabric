#!/usr/bin/env python3
"""Build a section-target matrix for one parsed document using section-first segmentation."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.core.config import settings  # noqa: E402
from packages.db.models import ContentChunk, Document, DocumentPage  # noqa: E402
from packages.db.session import SessionLocal  # noqa: E402
from packages.storage.manager import StorageManager  # noqa: E402


TARGET_RULES = [
    ("fault_code", ("fault", "alarm", "trip", "故障", "报警", "代码")),
    ("fault_diagnostic_rule", ("diagnostic", "troubleshoot", "diagnosis", "排查", "诊断")),
    ("symptom", ("symptom", "现象", "症状")),
    ("parameter_spec", ("parameter", "setpoint", "setting", "threshold", "limit", "参数", "设定", "阈值", "限值")),
    ("performance_spec", ("capacity", "performance", "rating", "cop", "kw", "ton", "性能", "容量", "额定")),
    ("maintenance_procedure", ("maintenance", "service", "inspection", "保养", "维护", "检修", "维修")),
    ("application_guidance", ("application", "scope", "requirement", "audit", "planning", "安装", "适用", "要求", "审计", "规划")),
    ("operational_sequence", ("operation", "sequence", "control", "运行", "控制", "流程", "步骤")),
]

NOISY_OUTLINE_PATTERNS = (
    r"^[a-z0-9_\-.]+\.pdf$",
    r"^[a-z0-9_\-.]+\.jpg$",
    r"^[a-z0-9_\-.]+$",
    r"^\d{4,}_[a-z0-9_\-.]+$",
)

HEADER_NOISE_PATTERNS = [
    re.compile(r"^\d+(?:\.\d+)?\s+\d{4}\s+ASHRAE Handbook.*?(?:\(SI\)|\(IP\))?\s*", re.I),
    re.compile(r"^\d+(?:\.\d+)?\s+ASHRAE Handbook.*?(?:\(SI\)|\(IP\))?\s*", re.I),
    re.compile(r"^\d+(?:\.\d+)?\s+", re.I),
    re.compile(r"\s+\d+\.\d+$"),
]

GENERIC_HEADINGS = {"untitled", "chapter", "section"}
GENERIC_BOOK_TITLE_PATTERNS = (
    "systems and equipment",
    "hvac applications",
    "handbook—hv",
    "handbook-hv",
    "handbook—fundamentals",
    "handbook-fundamentals",
    "ashrae handbook",
)


@dataclass
class PageRecord:
    page_no: int
    page_text: str
    chunk_count: int
    chunk_texts: list[str]


@dataclass
class OutlineEntry:
    title: str
    page_start: int


@dataclass
class SectionRow:
    section_title: str
    page_start: int
    page_end: int
    chunk_count: int
    matched_types: list[str]
    confidence: str
    sample_text: str
    section_source: str


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\n", " ")).strip()


def load_rows(doc_id: str) -> tuple[Document, list[tuple[ContentChunk, DocumentPage]]]:
    db = SessionLocal()
    try:
        rows = list(
            db.query(ContentChunk, DocumentPage, Document)
            .join(DocumentPage, ContentChunk.page_id == DocumentPage.page_id)
            .join(Document, ContentChunk.doc_id == Document.doc_id)
            .filter(ContentChunk.doc_id == doc_id)
            .order_by(ContentChunk.page_no, ContentChunk.chunk_index)
            .all()
        )
    finally:
        db.close()
    if not rows:
        raise SystemExit(f"doc_id not found or has no chunks: {doc_id}")
    document = rows[0][2]
    return document, [(chunk, page) for chunk, page, _ in rows]


def build_page_records(rows: list[tuple[ContentChunk, DocumentPage]]) -> list[PageRecord]:
    pages: dict[int, PageRecord] = {}
    for chunk, page in rows:
        text = chunk.cleaned_text or chunk.text_excerpt or ""
        record = pages.setdefault(
            page.page_no,
            PageRecord(
                page_no=page.page_no,
                page_text=page.cleaned_text or page.raw_text or text,
                chunk_count=0,
                chunk_texts=[],
            ),
        )
        record.chunk_count += 1
        if text:
            record.chunk_texts.append(text)
    return [pages[key] for key in sorted(pages)]


def clean_outline_title(title: str) -> str:
    text = normalize(title)
    text = text.replace("\x00", "")
    text = re.sub(r"^[\-\s]+|[\-\s]+$", "", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text


def is_meaningful_outline_title(title: str) -> bool:
    lowered = title.lower()
    if not lowered or len(lowered) < 4:
        return False
    if any(re.match(pattern, lowered) for pattern in NOISY_OUTLINE_PATTERNS):
        return False
    if lowered.startswith("cover") or lowered.startswith("toc"):
        return False
    alpha_ratio = sum(ch.isalpha() for ch in title) / max(len(title), 1)
    return alpha_ratio >= 0.45 or any(token in lowered for token in ("chapter", "audit", "design", "system", "control", "application"))


def flatten_outline(items: list[Any], reader: PdfReader) -> list[OutlineEntry]:
    entries: list[OutlineEntry] = []
    stack = list(items)[::-1]
    while stack:
        item = stack.pop()
        if isinstance(item, list):
            stack.extend(reversed(item))
            continue
        if not hasattr(item, "get"):
            continue
        raw_title = item.get("/Title")
        if not raw_title:
            continue
        title = clean_outline_title(str(raw_title))
        if not is_meaningful_outline_title(title):
            continue
        try:
            page_no = int(reader.get_destination_page_number(item)) + 1
        except Exception:
            continue
        if page_no <= 0:
            continue
        entries.append(OutlineEntry(title=title, page_start=page_no))
    deduped: list[OutlineEntry] = []
    seen: set[tuple[str, int]] = set()
    for entry in sorted(entries, key=lambda item: (item.page_start, item.title.lower())):
        key = (entry.title.lower(), entry.page_start)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(entry)
    return deduped


def resolve_pdf_path(document: Document) -> Path | None:
    storage = StorageManager(settings.storage_root)
    path = storage.get_document_path(document.storage_path)
    return path if path.exists() else None


def load_outline_entries(document: Document) -> list[OutlineEntry]:
    path = resolve_pdf_path(document)
    if not path:
        return []
    try:
        reader = PdfReader(str(path))
    except Exception:
        return []
    outline = getattr(reader, "outline", None) or []
    if not isinstance(outline, list):
        return []
    entries = flatten_outline(outline, reader)
    if len(entries) < 3:
        return []
    meaningful_ratio = len(entries) / max(len(outline), 1)
    return entries if meaningful_ratio >= 0.25 else []


def page_lines(page_text: str) -> list[str]:
    return [line.strip() for line in page_text.splitlines() if line.strip()]


def clean_heading_candidate(text: str) -> str:
    candidate = normalize(text)
    for pattern in HEADER_NOISE_PATTERNS:
        candidate = pattern.sub("", candidate).strip()
    candidate = re.sub(r"\s{2,}", " ", candidate)
    candidate = candidate.strip(" -–—:•")
    return candidate


def is_heading_like(line: str) -> bool:
    if not line:
        return False
    candidate = clean_heading_candidate(line)
    if not candidate or len(candidate) < 4:
        return False
    lowered = candidate.lower()
    if lowered in GENERIC_HEADINGS:
        return False
    if any(token in lowered for token in GENERIC_BOOK_TITLE_PATTERNS):
        return False
    if "•" in line:
        return False
    if line.rstrip().endswith((".", ";", ":")) and not re.match(r"^\d+(?:\.\d+){0,2}\s+", line):
        return False
    alpha_count = sum(char.isalpha() for char in candidate)
    if alpha_count < 3:
        return False
    words = candidate.split()
    if len(words) > 14:
        return False
    if re.match(r"^(chapter|appendix)\b", lowered):
        return True
    if re.match(r"^\d+(?:\.\d+){0,2}\s+[A-Z0-9]", line):
        return True
    upper_ratio = sum(1 for ch in candidate if ch.isupper()) / max(sum(1 for ch in candidate if ch.isalpha()), 1)
    title_case_words = sum(1 for word in words if word[:1].isupper())
    if upper_ratio >= 0.75 and len(words) <= 12:
        return True
    return len(words) <= 8 and title_case_words >= max(2, len(words) - 1)


def extract_page_heading(record: PageRecord) -> str | None:
    lines = page_lines(record.page_text)
    if not lines:
        return None
    if len(lines) >= 2 and re.match(r"^\d+(?:\.\d+)?\s*chapter\b", lines[0], re.I):
        title = clean_heading_candidate(lines[1])
        return title or clean_heading_candidate(lines[0])
    for line in lines[:8]:
        candidate = clean_heading_candidate(line)
        lowered = candidate.lower()
        if any(token in lowered for token in GENERIC_BOOK_TITLE_PATTERNS):
            continue
        if is_heading_like(line):
            return candidate
    return None


def detect_types(text: str) -> list[str]:
    lowered = text.lower()
    matched = []
    for target, tokens in TARGET_RULES:
        if any(token in lowered for token in tokens):
            matched.append(target)
    return matched


def confidence_for(matches: list[str], span_pages: int, chunk_count: int) -> str:
    if not matches:
        return "none"
    richness = len(matches) + (1 if span_pages >= 2 else 0) + (1 if chunk_count >= 3 else 0)
    if richness >= 4:
        return "high"
    if richness >= 2:
        return "medium"
    return "low"


def outline_confidence_for(title: str, matches: list[str], chunk_count: int) -> str:
    if not matches:
        return "none"
    lowered = title.lower()
    if len(matches) >= 2:
        return "high"
    if any(token in lowered for token in ("planning", "conducting", "report", "audit", "application", "selection", "control")):
        return "medium"
    return confidence_for(matches, 1, chunk_count)


def build_sections_from_outline(pages: list[PageRecord], entries: list[OutlineEntry]) -> list[SectionRow]:
    if not pages or not entries:
        return []
    page_map = {record.page_no: record for record in pages}
    page_numbers = [record.page_no for record in pages]
    max_page = max(page_numbers)
    sections: list[SectionRow] = []
    for idx, entry in enumerate(entries):
        start = entry.page_start
        next_start = entries[idx + 1].page_start if idx + 1 < len(entries) else max_page + 1
        if start not in page_map:
            continue
        end = min(next_start - 1, max_page)
        segment = [page_map[page_no] for page_no in page_numbers if start <= page_no <= end]
        if not segment:
            continue
        sample = normalize(" ".join(part.page_text for part in segment))[:320]
        chunk_count = sum(part.chunk_count for part in segment)
        matched = detect_types(f"{entry.title} {sample[:1400]}")
        sections.append(
            SectionRow(
                section_title=entry.title,
                page_start=start,
                page_end=segment[-1].page_no,
                chunk_count=chunk_count,
                matched_types=matched,
                confidence=outline_confidence_for(entry.title, matched, chunk_count),
                sample_text=sample,
                section_source="pdf_outline",
            )
        )
    return sections


def build_sections_from_page_headings(pages: list[PageRecord]) -> list[SectionRow]:
    sections: list[SectionRow] = []
    current_title = ""
    current_pages: list[PageRecord] = []

    def flush() -> None:
        nonlocal current_title, current_pages
        if not current_pages:
            return
        joined = normalize(" ".join(page.page_text for page in current_pages))
        chunk_count = sum(page.chunk_count for page in current_pages)
        matched = detect_types(f"{current_title} {joined[:1600]}")
        sections.append(
            SectionRow(
                section_title=current_title or f"pages_{current_pages[0].page_no}_{current_pages[-1].page_no}",
                page_start=current_pages[0].page_no,
                page_end=current_pages[-1].page_no,
                chunk_count=chunk_count,
                matched_types=matched,
                confidence=confidence_for(matched, current_pages[-1].page_no - current_pages[0].page_no + 1, chunk_count),
                sample_text=joined[:320],
                section_source="page_heading",
            )
        )
        current_title = ""
        current_pages = []

    for record in pages:
        heading = extract_page_heading(record)
        if heading and current_pages and heading.lower() != current_title.lower():
            flush()
        if not current_pages:
            current_title = heading or current_title or f"pages_{record.page_no}"
        elif heading and not current_title:
            current_title = heading
        current_pages.append(record)
    flush()
    return sections


def build_sections(rows: list[tuple[ContentChunk, DocumentPage]], document: Document) -> tuple[list[SectionRow], str]:
    pages = build_page_records(rows)
    outline_entries = load_outline_entries(document)
    if outline_entries:
        sections = build_sections_from_outline(pages, outline_entries)
        if sections:
            return sections, "pdf_outline"
    return build_sections_from_page_headings(pages), "page_heading"


def render_markdown(doc_name: str, doc_id: str, sections: list[SectionRow], strategy: str) -> str:
    lines = [
        "# Section Target Matrix",
        "",
        f"- Document: `{doc_name}`",
        f"- Doc ID: `{doc_id}`",
        f"- Section count: `{len(sections)}`",
        f"- Segmentation strategy: `{strategy}`",
        "",
        "| Section | Pages | Chunks | Candidate Knowledge Types | Confidence | Source | Sample |",
        "|---|---:|---:|---|---|---|---|",
    ]
    for item in sections:
        lines.append(
            f"| {item.section_title[:80]} | {item.page_start}-{item.page_end} | {item.chunk_count} | "
            f"{', '.join(item.matched_types) or '-'} | {item.confidence} | {item.section_source} | {item.sample_text[:140].replace('|','/')} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doc-id", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    document, rows = load_rows(args.doc_id)
    sections, strategy = build_sections(rows, document)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "doc_id": args.doc_id,
        "doc_name": document.file_name,
        "segmentation_strategy": strategy,
        "source_pdf": str(resolve_pdf_path(document) or ""),
        "sections": [
            {
                "section_title": item.section_title,
                "page_start": item.page_start,
                "page_end": item.page_end,
                "chunk_count": item.chunk_count,
                "candidate_knowledge_types": item.matched_types,
                "confidence": item.confidence,
                "sample_text": item.sample_text,
                "section_source": item.section_source,
            }
            for item in sections
        ],
        "candidate_type_counts": dict(Counter(t for item in sections for t in item.matched_types)),
    }
    (output_dir / "section_target_matrix.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "SECTION_TARGET_MATRIX.md").write_text(render_markdown(document.file_name, args.doc_id, sections, strategy), encoding="utf-8")
    print(output_dir / "SECTION_TARGET_MATRIX.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
