#!/usr/bin/env python3
"""Run ASHRAE Guideline 36 official-standard extraction for selected sections."""

from __future__ import annotations

import argparse
import copy
import hashlib
import http.client
import json
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator
from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.llm_compiler import (  # noqa: E402
    OpenAICompatibleBackend,
    _request_json_completion,
    repair_json_response_with_backend,
    response_content_text,
)
from packages.compiler.rule_compiler import stable_candidate_id  # noqa: E402
from packages.db.models import ContentChunk, Document, DocumentPage  # noqa: E402
from packages.db.session import SessionLocal  # noqa: E402
from scripts.llm_backend_config import load_backend  # noqa: E402

STANDARD_ID = "ASHRAE Guideline 36-2021"
ALLOWED_TYPES = (
    "operational_sequence",
    "parameter_spec",
    "fault_diagnostic_rule",
    "commissioning_step",
    "application_guidance",
)


class Guideline36Candidate(BaseModel):
    knowledge_type: Literal[
        "operational_sequence",
        "parameter_spec",
        "fault_diagnostic_rule",
        "commissioning_step",
        "application_guidance",
    ]
    title: str
    section_id: str
    section_title: str | None = None
    equipment_scope: str | None = None
    summary: str
    trigger_condition: str | None = None
    required_behavior: str | None = None
    configurable_values: list[str] = Field(default_factory=list)
    fault_condition: str | None = None
    commissioning_check: str | None = None
    evidence_quote: str
    page_hint: int | None = None
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("configurable_values", mode="before")
    @classmethod
    def _coerce_configurable_values(cls, value):
        if value is None:
            return []
        return value

    @field_validator("title", "section_id", "summary", "evidence_quote", mode="before")
    @classmethod
    def _coerce_required_text(cls, value):
        if value is None:
            return ""
        return value


class Guideline36ExtractionResponse(BaseModel):
    candidates: list[Guideline36Candidate] = Field(default_factory=list)
    skipped_reason: str | None = None


class Guideline36JudgeResponse(BaseModel):
    is_valid_guideline36_knowledge: bool
    reason: str
    category_if_not: str | None = Field(default=None)


@dataclass(frozen=True)
class SectionUnit:
    requested_section: str
    section_id: str
    section_title: str
    start_page: int
    end_page: int
    text: str
    chunk_ids: list[str]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    content = "\n".join(json.dumps(row, ensure_ascii=False, default=str) for row in rows)
    path.write_text((content + "\n") if content else "", encoding="utf-8")


def load_document_rows(doc_id: str) -> tuple[Document, list[DocumentPage], list[ContentChunk]]:
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.doc_id == doc_id).first()
        if doc is None:
            raise ValueError(f"Document not found: {doc_id}")
        pages = (
            db.query(DocumentPage)
            .filter(DocumentPage.doc_id == doc_id)
            .order_by(DocumentPage.page_no)
            .all()
        )
        chunks = (
            db.query(ContentChunk)
            .filter(ContentChunk.doc_id == doc_id)
            .order_by(ContentChunk.page_no, ContentChunk.chunk_index)
            .all()
        )
        return doc, pages, chunks
    finally:
        db.close()


def validate_official_ashrae_doc(doc: Document, pages: list[DocumentPage]) -> None:
    sample = " ".join((page.cleaned_text or "") for page in pages[:8])
    if "ASHRAE Guideline 36" not in sample:
        raise ValueError("This runner is scoped to official ASHRAE Guideline 36 documents only")


def build_section_units(doc: Document, pages: list[DocumentPage], chunks: list[ContentChunk], requested: list[str]) -> list[SectionUnit]:
    outline = extract_outline(doc)
    page_by_no = {page.page_no: page for page in pages}
    units = []
    for section in requested:
        start = find_outline_start(outline, section)
        end_page = find_outline_end_page(outline, start, len(pages))
        text_parts = []
        for page_no in range(start["page"], end_page + 1):
            page = page_by_no.get(page_no)
            if page:
                text_parts.append(f"[[page={page_no}]]\n{sanitize_text(page.cleaned_text or '')}")
        scoped_chunks = [chunk.chunk_id for chunk in chunks if start["page"] <= chunk.page_no <= end_page]
        section_text = trim_to_section_start("\n\n".join(text_parts), section)
        units.append(
            SectionUnit(
                requested_section=section,
                section_id=section,
                section_title=clean_section_title(start["title"]),
                start_page=start["page"],
                end_page=end_page,
                text=section_text,
                chunk_ids=scoped_chunks,
            )
        )
    return units


def extract_outline(doc: Document) -> list[dict[str, Any]]:
    path = Path("storage/documents") / doc.storage_path
    reader = PdfReader(str(path))
    rows: list[dict[str, Any]] = []

    def walk(items: list[Any], depth: int = 0) -> None:
        for item in items:
            if isinstance(item, list):
                walk(item, depth + 1)
                continue
            try:
                title = str(getattr(item, "title", item))
                page = reader.get_destination_page_number(item) + 1
            except Exception:
                continue
            rows.append({"title": title, "page": page, "depth": depth})

    walk(reader.outline)
    if not rows:
        raise ValueError("Guideline 36 PDF has no readable outline/bookmarks")
    return rows


def find_outline_start(outline: list[dict[str, Any]], section: str) -> dict[str, Any]:
    section_prefix = f"{section}."
    for row in outline:
        title = row["title"].replace("\u200e", "")
        if title.startswith(section_prefix) or title.startswith(f"{section} "):
            return row
    raise ValueError(f"Section {section} not found in outline")


def find_outline_end_page(outline: list[dict[str, Any]], start: dict[str, Any], max_page: int) -> int:
    start_index = outline.index(start)
    for row in outline[start_index + 1 :]:
        if row["depth"] <= start["depth"] and row["page"] > start["page"]:
            return row["page"] - 1
    return max_page


def clean_section_title(title: str) -> str:
    return re.sub(r"\s+", " ", title.replace("\u200e", "")).strip()


def trim_to_section_start(text: str, section: str) -> str:
    """Drop previous-section tail text that shares the first bookmarked page."""

    pattern = re.compile(rf"(?m)(^|[\n ]){re.escape(section)}(?:\.|\s)")
    match = pattern.search(text)
    if not match:
        return text
    return text[match.start() :].lstrip()


def sanitize_text(text: str) -> str:
    return "".join(char if char in "\n\r\t" or ord(char) >= 32 else " " for char in text)


def estimate_tokens(text: str) -> int:
    cjk = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    return int(cjk / 2 + (len(text) - cjk) / 4)


def build_extract_messages(unit: SectionUnit) -> list[dict[str, str]]:
    system = (
        "You are a senior HVAC controls engineer extracting official ASHRAE Guideline 36 knowledge. "
        "Extract concise, high-value structured knowledge from the provided section only. Treat this as an "
        "industry standard/guideline source, not an OEM manual. Preserve section citations and exact evidence. "
        "Allowed knowledge_type values: operational_sequence, parameter_spec, fault_diagnostic_rule, "
        "commissioning_step, application_guidance. Prefer actionable control logic: enable/disable logic, "
        "staging rules, trim-and-respond reset rules, alarm/fault equations, setpoints/timers/ranges, and "
        "commissioning or TAB checks. Do not extract foreword/legal text, generic definitions, repeated table of "
        "contents lines, bibliography, marketing language, or ungrounded paraphrases. For long sections, return "
        "the most operationally important items instead of one item per bullet. evidence_quote MUST be a SHORT "
        "verbatim contiguous substring copied from the section text, preferably the exact section heading line or "
        "one short requirement sentence. Do not use ellipses. Do not combine non-contiguous bullets into one quote. "
        "Never include facts in summary, trigger_condition, or required_behavior unless they are supported by "
        "evidence_quote. If a requirement has multiple alternatives (for example option a and option b), split "
        "them into separate candidates, one candidate per alternative. "
        "Keep evidence_quote under 35 words when possible. If you cannot quote it exactly, skip that item. "
        "Return strict JSON with fields candidates and skipped_reason."
    )
    user = (
        f"standard_id: {STANDARD_ID}\n"
        f"requested_section: {unit.requested_section}\n"
        f"section_title: {unit.section_title}\n"
        f"page_range: {unit.start_page}-{unit.end_page}\n\n"
        "Section text:\n"
        f"{unit.text}\n\n"
        "Return JSON shape:\n"
        '{"candidates":[{"knowledge_type":"operational_sequence","title":"...",'
        '"section_id":"5.20.2.2","section_title":"Plant Enable/Disable","equipment_scope":"...",'
        '"summary":"...","trigger_condition":"...","required_behavior":"...",'
        '"configurable_values":["..."],"fault_condition":null,"commissioning_check":null,'
        '"evidence_quote":"exact source quote","page_hint":172,"confidence":0.9}],'
        '"skipped_reason":null}'
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def build_bundle_extract_messages(units: list[SectionUnit]) -> list[dict[str, str]]:
    system = (
        "You are a senior HVAC controls engineer extracting official ASHRAE Guideline 36 knowledge. "
        "Use the full provided multi-section context to understand cross-references and repeated logic, then "
        "extract concise, high-value structured knowledge from the requested sections. Treat this as an industry "
        "standard/guideline source. Allowed knowledge_type values: operational_sequence, parameter_spec, "
        "fault_diagnostic_rule, commissioning_step, application_guidance. Prefer actionable control logic: "
        "enable/disable logic, staging rules, trim-and-respond reset rules, alarm/fault equations, "
        "setpoints/timers/ranges, and commissioning or TAB checks. Do not extract front matter, table-of-contents "
        "lines, bibliography, generic definitions without operational use, or ungrounded paraphrases. If the same "
        "knowledge appears in multiple sections, return the clearest canonical item once per applicable section. "
        "evidence_quote MUST be a SHORT verbatim contiguous substring copied from the section text. Do not use "
        "ellipses or combine non-contiguous bullets. Never include facts in summary, trigger_condition, or "
        "required_behavior unless they are supported by evidence_quote. If a requirement has multiple alternatives "
        "(for example option a and option b), split them into separate candidates, one candidate per alternative. "
        "Return strict JSON with fields candidates and skipped_reason."
    )
    user = (
        f"standard_id: {STANDARD_ID}\n"
        f"requested_sections: {', '.join(unit.requested_section for unit in units)}\n\n"
        "Multi-section text:\n"
        f"{build_bundle_text(units)}\n\n"
        "Return JSON shape:\n"
        '{"candidates":[{"knowledge_type":"operational_sequence","title":"...",'
        '"section_id":"5.20.2.2","section_title":"Plant Enable/Disable","equipment_scope":"...",'
        '"summary":"...","trigger_condition":"...","required_behavior":"...",'
        '"configurable_values":["..."],"fault_condition":null,"commissioning_check":null,'
        '"evidence_quote":"exact source quote","page_hint":172,"confidence":0.9}],'
        '"skipped_reason":null}'
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def build_bundle_text(units: list[SectionUnit]) -> str:
    parts = []
    for unit in units:
        parts.append(
            f"[[requested_section={unit.requested_section} page_range={unit.start_page}-{unit.end_page} "
            f"title={unit.section_title}]]\n{unit.text}"
        )
    return "\n\n".join(parts)


def extract_section(
    unit: SectionUnit,
    backend: OpenAICompatibleBackend,
    raw: list[dict[str, Any]],
    *,
    max_candidates: int,
) -> list[Guideline36Candidate]:
    print(
        f"extracting section {unit.requested_section} pages={unit.start_page}-{unit.end_page} "
        f"tokens~{estimate_tokens(unit.text)}",
        flush=True,
    )
    response = request_json_completion_with_retry(
        build_extract_messages(unit),
        backend,
        response_format={"type": "json_object"},
        recorder=lambda payload: raw.append({"section": unit.requested_section, **redact_raw_request(payload)}),
    )
    parsed = Guideline36ExtractionResponse.model_validate(response)
    print(f"section {unit.requested_section} returned {len(parsed.candidates)} candidates", flush=True)
    return parsed.candidates[:max_candidates]


def extract_section_bundle(
    units: list[SectionUnit],
    backend: OpenAICompatibleBackend,
    raw: list[dict[str, Any]],
    *,
    max_candidates_per_section: int,
) -> list[Guideline36Candidate]:
    sections = ",".join(unit.requested_section for unit in units)
    bundle_text = build_bundle_text(units)
    print(f"extracting bundle sections={sections} tokens~{estimate_tokens(bundle_text)}", flush=True)
    response = request_json_completion_with_retry(
        build_bundle_extract_messages(units),
        backend,
        response_format={"type": "json_object"},
        recorder=lambda payload: raw.append({"sections": sections, "extract_mode": "bundle", **redact_raw_request(payload)}),
    )
    parsed = Guideline36ExtractionResponse.model_validate(response)
    print(f"bundle sections={sections} returned {len(parsed.candidates)} candidates", flush=True)
    return cap_candidates_per_requested_section(parsed.candidates, units, max_candidates_per_section)


def cap_candidates_per_requested_section(
    candidates: list[Guideline36Candidate],
    units: list[SectionUnit],
    max_candidates: int,
) -> list[Guideline36Candidate]:
    counts = Counter()
    capped = []
    requested = [unit.requested_section for unit in units]
    for candidate in candidates:
        bucket = requested_bucket(candidate.section_id, requested)
        if counts[bucket] >= max_candidates:
            continue
        counts[bucket] += 1
        capped.append(candidate)
    return capped


def requested_bucket(section_id: str, requested: list[str]) -> str:
    for section in sorted(requested, key=len, reverse=True):
        if section_id == section or section_id.startswith(f"{section}."):
            return section
    return "other"


def request_json_completion_with_retry(
    messages: list[dict[str, str]],
    backend: OpenAICompatibleBackend,
    *,
    response_format: dict[str, Any],
    recorder,
    attempts: int = 3,
) -> dict[str, Any]:
    last_error: Exception | None = None
    last_attempt_raw: dict[str, Any] = {}

    def _record(value: dict[str, Any]) -> None:
        last_attempt_raw.clear()
        last_attempt_raw.update(value)
        recorder(value)

    for attempt in range(1, attempts + 1):
        try:
            return _request_json_completion(
                messages,
                backend,
                response_format=response_format,
                recorder=_record,
            )
        except (RuntimeError, http.client.IncompleteRead, TimeoutError, OSError) as exc:
            if last_attempt_raw.get("response"):
                content = response_content_text(last_attempt_raw["response"])
                if content and len(content) <= 20000:
                    try:
                        return repair_json_response_with_backend(content, backend, recorder=_record)
                    except Exception:
                        pass
            last_error = exc
            if not _is_retryable_llm_error(exc) or attempt == attempts:
                raise
            print(f"LLM transient error ({exc}); retrying {attempt + 1}/{attempts}", flush=True)
    raise RuntimeError(f"LLM request failed after {attempts} attempts: {last_error}")


def _is_retryable_llm_error(exc: Exception) -> bool:
    if isinstance(exc, (http.client.IncompleteRead, TimeoutError, OSError)):
        return True
    return isinstance(exc, RuntimeError) and "empty content" in str(exc).lower()


def redact_raw_request(payload: dict[str, Any]) -> dict[str, Any]:
    """Avoid persisting copyrighted ASHRAE section text in raw request logs."""

    redacted = copy.deepcopy(payload)
    request_payload = redacted.get("request")
    if isinstance(request_payload, dict) and isinstance(request_payload.get("messages"), list):
        for message in request_payload["messages"]:
            if not isinstance(message, dict):
                continue
            content = str(message.get("content") or "")
            message["content_sha1"] = sha1_text(content)
            message["content_chars"] = len(content)
            if message.get("role") == "user":
                message["content"] = "[redacted: ASHRAE section text omitted from artifact]"
    return redacted


def sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def build_raw_entries(
    candidates: list[Guideline36Candidate],
    doc: Document,
    backend: OpenAICompatibleBackend,
) -> list[dict[str, Any]]:
    rows = []
    for item in candidates:
        payload = item.model_dump()
        canonical = canonical_key(payload)
        rows.append(
            {
                "candidate_id": stable_candidate_id(doc.doc_id, STANDARD_ID, canonical, payload["evidence_quote"]),
                "domain_id": doc.source_domain,
                "doc_id": doc.doc_id,
                "doc_name": doc.file_name,
                "authority_level": "industry_standard",
                "standard_id": STANDARD_ID,
                "knowledge_object_type": payload["knowledge_type"],
                "canonical_key_candidate": canonical,
                "structured_payload_candidate": {key: value for key, value in payload.items() if key != "confidence"},
                "confidence_score": round(float(payload.get("confidence") or 0.0), 3),
                "review_status": "candidate",
                "compile_metadata": {"method": "ashrae_guideline36_section_compiler", "model": backend.model, "backend_name": backend.name},
                "evidence_quote": payload["evidence_quote"],
                "evidence_citation": f"{STANDARD_ID} §{payload['section_id']}",
            }
        )
    return rows


def canonical_key(payload: dict[str, Any]) -> str:
    title = slugify(payload.get("title") or payload.get("summary") or payload["section_id"])
    return f"ashrae:g36:{slugify(payload['knowledge_type'])}:{slugify(payload['section_id'])}:{title}"


def slugify(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", str(value).lower()).strip("_") or "item"


def anchor_candidates(
    raw_entries: list[dict[str, Any]],
    chunks: list[ContentChunk],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    chunk_index = [(chunk, normalize_anchor_text(chunk.cleaned_text or chunk.text_excerpt or ""), compact_anchor_text(chunk.cleaned_text or chunk.text_excerpt or "")) for chunk in chunks]
    anchored, rejected = [], []
    for entry in raw_entries:
        quote = entry.get("evidence_quote") or ""
        matches = find_matches(quote, chunk_index)
        entry_for_anchor = entry
        match_mode = "single_chunk"
        if not matches:
            entry_for_anchor, matches = repair_anchor_across_adjacent_chunks(entry, chunks)
            match_mode = str(entry_for_anchor.get("_anchor_match_mode") or match_mode)
        if not matches or is_weak_section_only_quote(entry, quote):
            entry_for_anchor, matches = repair_anchor_with_section_line(entry, chunks)
            match_mode = str(entry_for_anchor.get("_anchor_match_mode") or match_mode)
        if not matches:
            rejected.append({**entry, "rejection_reason": "evidence_quote not verbatim in any chunk"})
            continue
        updated = copy.deepcopy(entry_for_anchor)
        updated.pop("_anchor_match_mode", None)
        updated["source_chunk_ids"] = [chunk.chunk_id for chunk in matches]
        updated["chunk_id"] = matches[0].chunk_id
        updated["page_no"] = matches[0].page_no
        updated["source_page_nos"] = sorted({chunk.page_no for chunk in matches})
        updated["evidence_text"] = updated["evidence_quote"]
        is_cross_source = len(matches) >= 2 and match_mode != "cross_chunk_span"
        updated["trust_level"] = "L4" if is_cross_source else "L3"
        updated["verification_reason"] = verification_reason(match_mode, len(matches), is_cross_source)
        anchored.append(updated)
    return anchored, rejected


def repair_anchor_across_adjacent_chunks(
    entry: dict[str, Any],
    chunks: list[ContentChunk],
) -> tuple[dict[str, Any], list[ContentChunk]]:
    quote = compact_anchor_text(str(entry.get("evidence_quote") or ""))
    if not quote:
        return entry, []
    for index, chunk in enumerate(chunks[:-1]):
        next_chunk = chunks[index + 1]
        if chunk.page_no != next_chunk.page_no:
            continue
        combined = compact_anchor_text(" ".join([chunk.cleaned_text or chunk.text_excerpt or "", next_chunk.cleaned_text or next_chunk.text_excerpt or ""]))
        if quote in combined:
            repaired = copy.deepcopy(entry)
            repaired["_anchor_match_mode"] = "cross_chunk_span"
            return repaired, [chunk, next_chunk]
    return entry, []


def verification_reason(match_mode: str, match_count: int, is_cross_source: bool) -> str:
    if is_cross_source:
        return f"cross-source corroboration: {match_count} chunks"
    if match_mode == "cross_chunk_span":
        return f"verbatim evidence_quote spans {match_count} adjacent chunks"
    if match_mode == "section_line_repair":
        return "repaired to verbatim section line evidence"
    return "single chunk verbatim evidence_quote match"


def repair_anchor_with_section_line(
    entry: dict[str, Any],
    chunks: list[ContentChunk],
) -> tuple[dict[str, Any], list[ContentChunk]]:
    section_id = str(entry.get("structured_payload_candidate", {}).get("section_id") or "").strip()
    if not section_id:
        return entry, []
    compact_section = compact_anchor_text(section_id)
    for chunk_position, chunk in enumerate(chunks):
        lines = (chunk.cleaned_text or chunk.text_excerpt or "").splitlines()
        for index, line in enumerate(lines):
            if not section_line_matches(line, section_id, compact_section):
                continue
            evidence = line.strip()
            if len(evidence) < len(section_id) + 5:
                next_line = first_nonempty_line(lines[index + 1 :])
                if not next_line and chunk_position + 1 < len(chunks):
                    next_line = first_nonempty_line((chunks[chunk_position + 1].cleaned_text or "").splitlines())
                if next_line:
                    evidence = f"{evidence} {next_line}".strip()
            repaired = copy.deepcopy(entry)
            repaired["evidence_quote"] = evidence
            repaired["anchor_repair_reason"] = "evidence_quote replaced with verbatim section heading line"
            repaired["_anchor_match_mode"] = "section_line_repair"
            return repaired, [chunk]
    return entry, []


def section_line_matches(line: str, section_id: str, compact_section: str) -> bool:
    pattern = rf"(^|\s){re.escape(section_id)}(\s|$|[.)\]:-])"
    if re.search(pattern, line.strip(), flags=re.IGNORECASE):
        return True
    compact_line = compact_anchor_text(line)
    return compact_line == compact_section


def first_nonempty_line(lines: list[str]) -> str:
    for line in lines:
        if line.strip():
            return line.strip()
    return ""


def is_weak_section_only_quote(entry: dict[str, Any], quote: str) -> bool:
    section_id = str(entry.get("structured_payload_candidate", {}).get("section_id") or "").strip()
    if not section_id:
        return False
    return compact_anchor_text(quote) in {compact_anchor_text(section_id), compact_anchor_text(f"{section_id}.")}


def normalize_anchor_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower()).strip(" \t\r\n.,;:!?，。；：！？、")


def compact_anchor_text(text: str) -> str:
    text = text.lower().replace("％", "%").replace("（", "(").replace("）", ")")
    text = text.replace("–", "-").replace("—", "-").replace("‑", "-")
    return re.sub(r"[\s\u00a0，。；、,.;:]", "", text)


def find_matches(text: str, chunk_index: list[tuple[ContentChunk, str, str]]) -> list[ContentChunk]:
    normalized = normalize_anchor_text(text)
    compact = compact_anchor_text(text)
    return [chunk for chunk, chunk_text, compact_text in chunk_index if normalized and (normalized in chunk_text or compact in compact_text)]


def build_judge_messages(candidate: dict[str, Any]) -> list[dict[str, str]]:
    payload = candidate["structured_payload_candidate"]
    content = (
        "Validate whether this extracted item is useful, grounded ASHRAE Guideline 36 operational knowledge.\n\n"
        "ACCEPT if it captures a real control sequence, configurable control parameter, fault diagnostic rule, "
        "commissioning/TAB check, or applicability rule from the guideline. REJECT if it is only legal/front matter, "
        "table-of-contents text, a generic definition without operational use, duplicated/noisy extraction, or if the "
        "evidence does not support the summary.\n\n"
        f"knowledge_type: {candidate['knowledge_object_type']}\n"
        f"title: {payload.get('title')}\n"
        f"section_id: {payload.get('section_id')}\n"
        f"summary: {payload.get('summary')}\n"
        f"evidence: \"{candidate.get('evidence_quote')}\"\n"
        f"source_pages: {candidate.get('source_page_nos')}\n\n"
        'Reply with {"is_valid_guideline36_knowledge":true|false,"reason":"<short reason>",'
        '"category_if_not":null|"front_matter"|"toc"|"generic_definition"|"unsupported"|"duplicate"|"other"}.'
    )
    return [{"role": "system", "content": "You are an HVAC standards reviewer. Reply only with strict JSON."}, {"role": "user", "content": content}]


def judge_candidates(candidates: list[dict[str, Any]], backend: OpenAICompatibleBackend) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    accepted, rejected, raw = [], [], []
    for index, candidate in enumerate(candidates, start=1):
        print(f"judging {index}/{len(candidates)} {candidate['canonical_key_candidate']}", flush=True)
        result = request_json_completion_with_retry(
            build_judge_messages(candidate),
            backend,
            response_format={"type": "json_object"},
            recorder=lambda payload, candidate_id=candidate["candidate_id"]: raw.append({"candidate_id": candidate_id, **payload}),
        )
        verdict = Guideline36JudgeResponse.model_validate(result)
        updated = {**candidate, "judge_reason": verdict.reason}
        if verdict.is_valid_guideline36_knowledge:
            accepted.append({**updated, "judge_verdict": "accepted"})
        else:
            rejected.append({**updated, "judge_verdict": "rejected_by_judge", "judge_category": verdict.category_if_not})
    return accepted, rejected, raw


def dedup_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        groups.setdefault(candidate["canonical_key_candidate"], []).append(candidate)
    final = []
    for group in groups.values():
        best = max(group, key=lambda row: float(row.get("confidence_score") or 0.0))
        merged = copy.deepcopy(best)
        chunk_ids = list(dict.fromkeys(chunk for row in group for chunk in row.get("source_chunk_ids", [])))
        merged["source_chunk_ids"] = chunk_ids
        if len(chunk_ids) >= 2:
            merged["trust_level"] = "L4"
            merged["verification_reason"] = f"cross-source corroboration: {len(chunk_ids)} chunks"
        final.append(merged)
    return sorted(final, key=lambda row: (row.get("page_no") or 0, row["canonical_key_candidate"]))


def usage_tokens(raw: list[dict[str, Any]]) -> dict[str, int]:
    usages = [item.get("response", {}).get("usage", {}) for item in raw]
    prompt = sum(int(item.get("prompt_tokens") or 0) for item in usages)
    completion = sum(int(item.get("completion_tokens") or 0) for item in usages)
    return {"prompt_tokens": prompt, "completion_tokens": completion, "total_tokens": prompt + completion, "request_count": len(raw)}


def estimate_cost(raw: list[dict[str, Any]], pricing: dict[str, Any]) -> float:
    tokens = usage_tokens(raw)
    return round(tokens["prompt_tokens"] / 1000 * float(pricing.get("prompt_price_rmb_per_1k") or 0) + tokens["completion_tokens"] / 1000 * float(pricing.get("completion_price_rmb_per_1k") or 0), 6)


def build_summary(args, doc, units, timings, artifacts, backends, pricing) -> dict[str, Any]:
    final, raw_entries, anchored, anchor_rejected, judge_rejected, raw_extract, raw_judge = artifacts
    raw_count = len(raw_entries)
    anchor_rate = len(anchored) / raw_count * 100 if raw_count else 0.0
    judge_rate = len(final) / len(anchored) * 100 if anchored else 0.0
    covered = sorted({row["structured_payload_candidate"]["section_id"].split(".")[0] for row in final})
    requested_covered = {
        section: any(str(row["structured_payload_candidate"]["section_id"]).startswith(section) for row in final)
        for section in args.sections.split(",")
    }
    extract_backend, judge_backend = backends
    extract_pricing, judge_pricing = pricing
    extract_cost = estimate_cost(raw_extract, extract_pricing)
    judge_cost = estimate_cost(raw_judge, judge_pricing)
    wallclock_limit = max(900, 20 * (len(raw_extract) + len(raw_judge)))
    gates = {
        "G1": {"status": "PASS" if anchor_rate >= 80 else "FAIL", "value": anchor_rate},
        "G2": {"status": "PASS" if judge_rate >= 60 else "FAIL", "value": judge_rate},
        "G3": {"status": "PASS" if all(requested_covered.values()) else "FAIL", "value": requested_covered},
        "G4": {
            "status": "PASS" if timings["total_seconds"] <= wallclock_limit else "FAIL",
            "value": timings["total_seconds"],
            "limit_seconds": wallclock_limit,
        },
    }
    return {
        "run_id": make_run_id(doc.file_name),
        "standard_id": STANDARD_ID,
        "manual": doc.file_name,
        "doc_id": doc.doc_id,
        "sections": [unit.requested_section for unit in units],
        "extract_mode": getattr(args, "extract_mode", "section"),
        "section_units": [unit.__dict__ | {"text": f"{len(unit.text)} chars"} for unit in units],
        "extract_backend": extract_backend.name,
        "extract_model": extract_backend.model,
        "judge_backend": judge_backend.name,
        "judge_model": judge_backend.model,
        "extract_usage": usage_tokens(raw_extract),
        "judge_usage": usage_tokens(raw_judge),
        "extract_cost_rmb": extract_cost,
        "judge_cost_rmb": judge_cost,
        "total_cost_rmb": extract_cost + judge_cost,
        "raw_candidates": raw_count,
        "anchor_passed": len(anchored),
        "anchor_rejected": len(anchor_rejected),
        "judge_accepted": len(final),
        "judge_rejected": len(judge_rejected),
        "judge_rejection_breakdown": dict(Counter(row.get("judge_category") or "other" for row in judge_rejected)),
        "final_by_type": dict(Counter(row["knowledge_object_type"] for row in final)),
        "l4_final": sum(1 for row in final if row.get("trust_level") == "L4"),
        "l3_final": sum(1 for row in final if row.get("trust_level") == "L3"),
        "covered_top_sections": covered,
        "requested_covered": requested_covered,
        "timings": timings,
        "gates": gates,
    }


def make_run_id(file_name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", Path(file_name).stem.lower()).strip("_")
    return f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{slug}_ashrae_g36"


def build_report(summary: dict[str, Any], samples: dict[str, list[str]]) -> str:
    breakdown = ", ".join(f"{k}: {v}" for k, v in summary["judge_rejection_breakdown"].items()) or "none"
    by_type = ", ".join(f"{k}: {v}" for k, v in summary["final_by_type"].items()) or "none"
    gates = summary["gates"]
    return f"""# ASHRAE Guideline 36 Vertical Run Report

**Run ID:** {summary["run_id"]}
**Standard:** {summary["standard_id"]}
**Document:** {summary["manual"]}
**Sections:** {", ".join(summary["sections"])}
**Architecture:** {summary["extract_mode"]} official-standard extraction + judge + verbatim chunk anchoring
**Extract backend:** {summary["extract_backend"]} / {summary["extract_model"]}
**Judge backend:** {summary["judge_backend"]} / {summary["judge_model"]}

## Token / Cost

| Metric | Value |
|--------|-------|
| Extract input tokens | {summary["extract_usage"]["prompt_tokens"]} |
| Extract output tokens | {summary["extract_usage"]["completion_tokens"]} |
| Judge total tokens | {summary["judge_usage"]["total_tokens"]} |
| Total cost | ¥{summary["total_cost_rmb"]:.4f} |
| Total wallclock | {summary["timings"]["total_seconds"]:.2f}s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Extraction calls | {summary["extract_usage"].get("request_count", len(summary["sections"]))} |
| Raw candidates | {summary["raw_candidates"]} |
| Anchor passed | {summary["anchor_passed"]} |
| Anchor rejected | {summary["anchor_rejected"]} |
| Judge accepted | {summary["judge_accepted"]} |
| Judge rejected | {summary["judge_rejected"]} |
| Judge rejection breakdown | {breakdown} |
| Final by type | {by_type} |
| L4 / L3 | {summary["l4_final"]} / {summary["l3_final"]} |

## Section Coverage

{chr(10).join(f"- {section}: {'covered' if ok else 'missing'}" for section, ok in summary["requested_covered"].items())}

## Samples

### Accepted
{chr(10).join(samples["accepted"]) or "None"}

### Anchor Rejected
{chr(10).join(samples["anchor_rejected"]) or "None"}

### Judge Rejected
{chr(10).join(samples["judge_rejected"]) or "None"}

## Stability Gates

- G1 anchor_match_rate >= 80%: {gates["G1"]["status"]} ({gates["G1"]["value"]:.1f}%)
- G2 judge_acceptance_rate >= 60%: {gates["G2"]["status"]} ({gates["G2"]["value"]:.1f}%)
- G3 every requested section has accepted knowledge: {gates["G3"]["status"]} ({gates["G3"]["value"]})
- G4 total_wallclock within scaled budget: {gates["G4"]["status"]} ({gates["G4"]["value"]:.2f}s / {gates["G4"]["limit_seconds"]:.0f}s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and whether each item should map to sw_base_model control/operation semantics.
"""


def build_samples(final, anchor_rejected, judge_rejected) -> dict[str, list[str]]:
    return {
        "accepted": [f"- p{row.get('page_no')}, §{row['structured_payload_candidate']['section_id']}, {row['knowledge_object_type']}: {row['structured_payload_candidate']['title']}" for row in final[:15]],
        "anchor_rejected": [f"- §{row['structured_payload_candidate'].get('section_id')}: {row['structured_payload_candidate'].get('title')} | {row.get('rejection_reason')}" for row in anchor_rejected[:10]],
        "judge_rejected": [f"- §{row['structured_payload_candidate'].get('section_id')}: {row['structured_payload_candidate'].get('title')} | {row.get('judge_category')}: {row.get('judge_reason')}" for row in judge_rejected[:10]],
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    start = time.monotonic()
    extract_backend, extract_pricing = load_backend(args.extract_backend)
    judge_backend, judge_pricing = load_backend(args.judge_backend)
    if extract_backend.name == judge_backend.name:
        raise ValueError("extract and judge backends must be different")
    doc, pages, chunks = load_document_rows(args.doc_id)
    validate_official_ashrae_doc(doc, pages)
    sections = [item.strip() for item in args.sections.split(",") if item.strip()]
    units = build_section_units(doc, pages, chunks, sections)
    raw_extract: list[dict[str, Any]] = []
    for unit in units:
        if estimate_tokens(unit.text) > args.max_section_tokens:
            raise ValueError(f"Section {unit.requested_section} exceeds token cap")
    extracted = extract_units(args, units, extract_backend, raw_extract)
    raw_entries = build_raw_entries(extracted, doc, extract_backend)
    print(f"anchoring {len(raw_entries)} raw candidates", flush=True)
    anchored, anchor_rejected = anchor_candidates(raw_entries, chunks)
    print(f"anchor_passed={len(anchored)} anchor_rejected={len(anchor_rejected)}", flush=True)
    accepted, judge_rejected, raw_judge = judge_candidates(anchored, judge_backend)
    final = dedup_candidates(accepted)
    timings = {"total_seconds": time.monotonic() - start}
    artifacts = (final, raw_entries, anchored, anchor_rejected, judge_rejected, raw_extract, raw_judge)
    summary = build_summary(args, doc, units, timings, artifacts, (extract_backend, judge_backend), (extract_pricing, judge_pricing))
    write_outputs(args, summary, units, artifacts)
    return summary


def extract_units(
    args: argparse.Namespace,
    units: list[SectionUnit],
    backend: OpenAICompatibleBackend,
    raw_extract: list[dict[str, Any]],
) -> list[Guideline36Candidate]:
    if args.extract_mode == "bundle":
        bundle_text = build_bundle_text(units)
        if estimate_tokens(bundle_text) > args.max_section_tokens:
            raise ValueError("Section bundle exceeds token cap")
        return extract_section_bundle(
            units,
            backend,
            raw_extract,
            max_candidates_per_section=args.max_candidates_per_section,
        )
    extracted: list[Guideline36Candidate] = []
    for unit in units:
        extracted.extend(extract_section(unit, backend, raw_extract, max_candidates=args.max_candidates_per_section))
    return extracted


def write_outputs(args, summary: dict[str, Any], units: list[SectionUnit], artifacts: tuple[Any, ...]) -> None:
    final, raw_entries, anchored, anchor_rejected, judge_rejected, raw_extract, raw_judge = artifacts
    output_dir = Path(args.output_dir) / summary["run_id"]
    output_dir.mkdir(parents=True, exist_ok=False)
    write_jsonl(output_dir / "candidates_llm_raw.jsonl", raw_entries)
    write_jsonl(output_dir / "candidates_llm_anchor_passed.jsonl", anchored)
    write_jsonl(output_dir / "candidates_llm_verified.jsonl", final)
    write_jsonl(output_dir / "candidates_llm_rejected.jsonl", anchor_rejected)
    write_jsonl(output_dir / "candidates_llm_judge_rejected.jsonl", judge_rejected)
    write_jsonl(output_dir / "raw_extract_response.jsonl", raw_extract)
    write_jsonl(output_dir / "raw_judge_responses.jsonl", raw_judge)
    (output_dir / "section_units.json").write_text(json.dumps([public_section_unit(unit) for unit in units], ensure_ascii=False, indent=2), encoding="utf-8")
    samples = build_samples(final, anchor_rejected, judge_rejected)
    (output_dir / "REPORT.md").write_text(build_report(summary, samples), encoding="utf-8")
    summary["output_dir"] = str(output_dir)
    summary["report_path"] = str(output_dir / "REPORT.md")
    (output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def public_section_unit(unit: SectionUnit) -> dict[str, Any]:
    return {
        "requested_section": unit.requested_section,
        "section_id": unit.section_id,
        "section_title": unit.section_title,
        "start_page": unit.start_page,
        "end_page": unit.end_page,
        "text_chars": len(unit.text),
        "text_sha1": sha1_text(unit.text),
        "chunk_ids": unit.chunk_ids,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doc-id", required=True)
    parser.add_argument("--sections", default="5.1.14,5.20,5.21")
    parser.add_argument("--extract-backend", required=True)
    parser.add_argument("--judge-backend", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--budget-rmb", type=float, default=30.0)
    parser.add_argument("--max-section-tokens", type=int, default=250_000)
    parser.add_argument("--max-candidates-per-section", type=int, default=24)
    parser.add_argument("--extract-mode", choices=["section", "bundle"], default="section")
    return parser


def main(argv: list[str] | None = None) -> int:
    summary = run(build_parser().parse_args(argv))
    failed = [name for name, gate in summary["gates"].items() if gate["status"] != "PASS"]
    print(
        f"summary raw={summary['raw_candidates']} anchor_passed={summary['anchor_passed']} "
        f"verified={summary['judge_accepted']} L4={summary['l4_final']} cost=¥{summary['total_cost_rmb']:.4f} "
        f"report={summary['report_path']}"
    )
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
