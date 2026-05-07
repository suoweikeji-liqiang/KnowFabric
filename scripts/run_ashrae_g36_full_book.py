#!/usr/bin/env python3
"""Run ASHRAE Guideline 36 extraction as one full-book LLM pass plus one batch judge pass."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import time
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.llm_compiler import OpenAICompatibleBackend  # noqa: E402
from packages.db.models import ContentChunk, Document, DocumentPage  # noqa: E402
from scripts.run_ashrae_guideline36_vertical import (  # noqa: E402
    ALLOWED_TYPES,
    STANDARD_ID,
    Guideline36Candidate,
    Guideline36ExtractionResponse,
    anchor_candidates,
    build_bundle_text,
    build_raw_entries,
    build_samples,
    build_section_units,
    dedup_candidates,
    estimate_cost,
    estimate_tokens,
    load_backend,
    load_document_rows,
    make_run_id,
    redact_raw_request,
    request_json_completion_with_retry,
    sha1_text,
    usage_tokens,
    validate_official_ashrae_doc,
    write_jsonl,
)


class Guideline36BatchJudgeItem(BaseModel):
    candidate_id: str
    is_valid_guideline36_knowledge: bool
    reason: str
    category_if_not: str | None = Field(default=None)


class Guideline36BatchJudgeResponse(BaseModel):
    verdicts: list[Guideline36BatchJudgeItem] = Field(default_factory=list)


def assemble_full_book_text(chunks: list[ContentChunk]) -> str:
    parts = []
    for chunk in chunks:
        text = chunk.cleaned_text or chunk.text_excerpt or ""
        parts.append(f"[[page={chunk.page_no} chunk_id={chunk.chunk_id} chunk_index={chunk.chunk_index}]]")
        parts.append(sanitize_full_book_text(text))
    return "\n\n".join(parts)


def sanitize_full_book_text(text: str) -> str:
    return "".join(char if char in "\n\r\t" or ord(char) >= 32 else " " for char in text)


def build_full_book_extract_messages(
    doc: Document,
    full_book_text: str,
    *,
    target_candidates: int = 100,
    focus_sections: list[str] | None = None,
    focus_text: str = "",
) -> list[dict[str, str]]:
    focus_clause = build_focus_clause(focus_sections)
    system = (
        "You are a senior HVAC controls engineer extracting official ASHRAE Guideline 36 knowledge from the "
        "entire standard in one pass. Use the whole-book context to resolve cross-chapter references, repeated "
        "logic, and definitions. Treat chunks only as evidence anchors, not extraction boundaries. "
        f"{focus_clause}"
        f"Allowed knowledge_type values: {', '.join(ALLOWED_TYPES)}. Prefer high-value operational knowledge: "
        "control sequences, enable/disable logic, reset logic, staging logic, setpoints, timers, alarm/fault "
        "diagnostic rules, commissioning/TAB checks, and application rules. Do not extract front matter, legal "
        "text, table-of-contents lines, bibliography, generic definitions without operational use, or unsupported "
        "paraphrases. If the same knowledge appears multiple times, return it once with the clearest authoritative "
        "evidence_quote. evidence_quote MUST be a verbatim contiguous substring copied from the manual and it MUST "
        "support every important fact in summary, trigger_condition, required_behavior, configurable_values, "
        "fault_condition, or commissioning_check. For operational_sequence, quote the complete rule sentence or "
        "table row that includes the condition and commanded behavior. For fault_diagnostic_rule, quote the alarm "
        "or fault condition itself. For commissioning_step, quote the check or verification action. A section "
        "heading alone, a half sentence, an editor instruction such as retain/delete this section, or an "
        "introductory phrase is NOT sufficient evidence. Do not use ellipses. Do not combine non-contiguous "
        "bullets. If one exact quote cannot support the candidate, make the candidate narrower or skip it. If a "
        "requirement has alternatives, split them into separate candidates unless one exact quote supports the "
        f"combined item. Return at most {target_candidates} candidates. Prefer fewer high-confidence candidates with "
        "complete evidence over broad coverage with weak evidence. Keep evidence_quote concise, usually one complete "
        "sentence or one complete table row, not a paragraph. Preserve section_id and page_hint from nearby headings "
        "and [[page=...]] anchors. Return "
        "strict JSON with fields candidates and skipped_reason only."
    )
    user = (
        f"standard_id: {STANDARD_ID}\n"
        f"manual_filename: {doc.file_name}\n"
        "architecture: single-call full-book extraction\n\n"
        f"focus_sections: {', '.join(focus_sections or []) or 'all'}\n\n"
        f"{focus_text_block(focus_text)}"
        "Manual content with chunk anchors:\n"
        f"{full_book_text}\n\n"
        "Return JSON shape:\n"
        '{"candidates":[{"knowledge_type":"operational_sequence","title":"...",'
        '"section_id":"5.20.2.2","section_title":"Plant Enable/Disable","equipment_scope":"...",'
        '"summary":"...","trigger_condition":"...","required_behavior":"...",'
        '"configurable_values":["..."],"fault_condition":null,"commissioning_check":null,'
        '"evidence_quote":"exact source quote","page_hint":172,"confidence":0.9}],'
        '"skipped_reason":null}'
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def build_focus_clause(focus_sections: list[str] | None) -> str:
    if not focus_sections:
        return ""
    sections = ", ".join(focus_sections)
    return (
        f"FOCUS SCOPE: Extract ONLY knowledge whose primary section_id equals one of these sections or starts with "
        f"one of these section prefixes followed by a dot: {sections}. "
        "Use the rest of the manual only as context for definitions, cross-references, and terminology. Do not return "
        "candidates from outside the focus scope. Evidence quotes must come from the focus scope text, not from unrelated "
        "sections used only as context. "
    )


def focus_text_block(focus_text: str) -> str:
    if not focus_text:
        return ""
    return (
        "FOCUS SECTION TEXT (extract candidates from this section text only; full manual below is context):\n"
        f"{focus_text}\n\n"
    )


def extract_full_book(
    doc: Document,
    full_book_text: str,
    backend: OpenAICompatibleBackend,
    raw_extract: list[dict[str, Any]],
    *,
    target_candidates: int,
    focus_sections: list[str] | None = None,
    focus_text: str = "",
) -> list[Guideline36Candidate]:
    print(f"extracting full book tokens~{estimate_tokens(full_book_text)}", flush=True)
    response = request_json_completion_with_retry(
        build_full_book_extract_messages(
            doc,
            full_book_text,
            target_candidates=target_candidates,
            focus_sections=focus_sections,
            focus_text=focus_text,
        ),
        backend,
        response_format={"type": "json_object"},
        recorder=lambda payload: raw_extract.append({"extract_mode": "full_book", "focus_sections": focus_sections or [], **redact_raw_request(payload)}),
    )
    parsed = Guideline36ExtractionResponse.model_validate(response)
    print(f"full-book extraction returned {len(parsed.candidates)} candidates", flush=True)
    return parsed.candidates


def build_batch_judge_messages(candidates: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows = [judge_row(candidate) for candidate in candidates]
    system = (
        "You are an HVAC standards reviewer. Validate extracted ASHRAE Guideline 36 items in one batch. Reply only "
        "with strict JSON. Return exactly one verdict per candidate_id."
    )
    user = (
        "Accept an item only if it is useful, grounded ASHRAE Guideline 36 operational knowledge. Reject legal/front "
        "matter, TOC text, generic definitions without operational use, duplicated/noisy extraction, or summaries not "
        "supported by evidence.\n\n"
        "Allowed category_if_not values: null, front_matter, toc, generic_definition, unsupported, duplicate, other.\n\n"
        f"Candidates:\n{json.dumps(rows, ensure_ascii=False)}\n\n"
        'Reply shape: {"verdicts":[{"candidate_id":"...","is_valid_guideline36_knowledge":true,'
        '"reason":"short reason","category_if_not":null}]}'
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def judge_row(candidate: dict[str, Any]) -> dict[str, Any]:
    payload = candidate["structured_payload_candidate"]
    return {
        "candidate_id": candidate["candidate_id"],
        "knowledge_type": candidate["knowledge_object_type"],
        "title": payload.get("title"),
        "section_id": payload.get("section_id"),
        "summary": payload.get("summary"),
        "evidence_quote": candidate.get("evidence_quote"),
        "source_pages": candidate.get("source_page_nos"),
    }


def judge_candidates_batch(
    candidates: list[dict[str, Any]],
    backend: OpenAICompatibleBackend,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    raw: list[dict[str, Any]] = []
    if not candidates:
        return [], [], raw
    print(f"batch judging {len(candidates)} candidates", flush=True)
    response = request_json_completion_with_retry(
        build_batch_judge_messages(candidates),
        backend,
        response_format={"type": "json_object"},
        recorder=lambda payload: raw.append({"judge_mode": "batch", **redact_batch_judge_request(payload)}),
    )
    verdicts = Guideline36BatchJudgeResponse.model_validate(response).verdicts
    accepted, rejected = apply_batch_verdicts(candidates, verdicts)
    return accepted, rejected, raw


def apply_batch_verdicts(
    candidates: list[dict[str, Any]],
    verdicts: list[Guideline36BatchJudgeItem],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    verdict_by_id = {item.candidate_id: item for item in verdicts}
    accepted, rejected = [], []
    for candidate in candidates:
        verdict = verdict_by_id.get(candidate["candidate_id"])
        if verdict is None:
            rejected.append(reject_missing_verdict(candidate))
            continue
        updated = {**candidate, "judge_reason": verdict.reason}
        if verdict.is_valid_guideline36_knowledge:
            accepted.append({**updated, "judge_verdict": "accepted"})
        else:
            rejected.append({**updated, "judge_verdict": "rejected_by_judge", "judge_category": verdict.category_if_not})
    return accepted, rejected


def reject_missing_verdict(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        **candidate,
        "judge_verdict": "rejected_by_judge",
        "judge_category": "missing_verdict",
        "judge_reason": "batch judge response did not include this candidate_id",
    }


def filter_weak_evidence_candidates(candidates: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    passed, rejected = [], []
    for candidate in candidates:
        reason = weak_evidence_reason(candidate)
        if reason:
            rejected.append({**candidate, "rejection_reason": reason})
        else:
            passed.append(candidate)
    return passed, rejected


def weak_evidence_reason(candidate: dict[str, Any]) -> str | None:
    quote = str(candidate.get("evidence_quote") or "").strip()
    payload = candidate.get("structured_payload_candidate", {})
    knowledge_type = str(candidate.get("knowledge_object_type") or "")
    normalized = quote.lower()
    if contains_editor_instruction(normalized):
        return "weak evidence_quote: editor instruction, not operational requirement"
    if looks_like_heading_only(quote, payload):
        return "weak evidence_quote: section heading without supporting rule"
    if knowledge_type == "fault_diagnostic_rule" and missing_specific_fault_code(quote, payload):
        return "weak evidence_quote: fault evidence lacks the specific FC item"
    if knowledge_type == "commissioning_step" and not contains_commissioning_signal(normalized):
        return "weak evidence_quote: commissioning evidence lacks procedure/check action"
    if looks_like_incomplete_intro(normalized):
        return "weak evidence_quote: introductory fragment without complete rule"
    if knowledge_type in {"operational_sequence", "fault_diagnostic_rule", "commissioning_step"}:
        if len(re.findall(r"[A-Za-z0-9%]+", quote)) < 8:
            return "weak evidence_quote: too short to support structured summary"
        if not contains_rule_signal(normalized):
            return "weak evidence_quote: lacks rule/action signal"
    return None


def contains_editor_instruction(normalized: str) -> bool:
    markers = (
        "retain/delete",
        "retain or delete",
        "delete this section",
        "retain this section",
        "designer shall",
        "specifier shall",
        "choose one",
    )
    return any(marker in normalized for marker in markers)


def looks_like_incomplete_intro(normalized: str) -> bool:
    stripped = normalized.strip()
    if stripped.endswith(","):
        return True
    markers = ("the following are potential", "map loop output as follows")
    return any(marker in stripped for marker in markers)


def missing_specific_fault_code(quote: str, payload: dict[str, Any]) -> bool:
    title = str(payload.get("title") or "")
    expected = re.findall(r"fc#?\s*(\d+)", title, flags=re.IGNORECASE)
    if not expected:
        return False
    quote_compact = compact_evidence_text(quote)
    return not any(f"fc{number}" in quote_compact for number in expected)


def contains_commissioning_signal(normalized: str) -> bool:
    signals = (
        "configure",
        "throttle",
        "reduce",
        "increase",
        "note",
        "report",
        "verify",
        "test",
        "measure",
        "starting from",
        "in increments",
    )
    return any(signal in normalized for signal in signals)


def looks_like_heading_only(quote: str, payload: dict[str, Any]) -> bool:
    compact_quote = compact_evidence_text(quote)
    if not compact_quote:
        return True
    fields = [payload.get("section_id"), payload.get("title"), payload.get("section_title")]
    field_texts = [compact_evidence_text(str(value)) for value in fields if value]
    if compact_quote in field_texts:
        return True
    return len(compact_quote) < 80 and any(compact_quote.endswith(text) for text in field_texts)


def compact_evidence_text(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9%]+", "", text.lower())


def contains_rule_signal(normalized: str) -> bool:
    signals = (
        "shall",
        "must",
        "should",
        "when",
        "whenever",
        "if",
        "enable",
        "disable",
        "reset",
        "stage",
        "start",
        "stop",
        "alarm",
        "fault",
        "open",
        "close",
        "modulat",
        "control",
        "setpoint",
        "command",
        "speed",
        "flow",
        "temperature",
        "pressure",
        "greater",
        "less",
        "below",
        "above",
        "=",
    )
    return any(signal in normalized for signal in signals)


def redact_batch_judge_request(payload: dict[str, Any]) -> dict[str, Any]:
    redacted = copy.deepcopy(payload)
    request_payload = redacted.get("request")
    if isinstance(request_payload, dict):
        request_payload["messages_sha1"] = sha1_text(json.dumps(request_payload.get("messages", []), ensure_ascii=False))
        request_payload["messages"] = "[redacted: candidate evidence omitted from raw judge artifact]"
    return redacted


def backend_with_overrides(
    backend: OpenAICompatibleBackend,
    *,
    max_tokens: int | None,
    timeout_seconds: int | None = None,
) -> OpenAICompatibleBackend:
    options = dict(backend.request_options or {})
    if max_tokens:
        options["max_tokens"] = max_tokens
    return replace(backend, request_options=options, timeout_seconds=timeout_seconds or backend.timeout_seconds)


def parse_focus_sections(value: str | None) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def candidate_in_focus(candidate: Guideline36Candidate, focus_sections: list[str]) -> bool:
    if not focus_sections:
        return True
    section_id = str(candidate.section_id or "")
    return any(section_id == section or section_id.startswith(f"{section}.") for section in focus_sections)


def filter_candidates_by_focus(candidates: list[Guideline36Candidate], focus_sections: list[str]) -> list[Guideline36Candidate]:
    if not focus_sections:
        return candidates
    filtered = [candidate for candidate in candidates if candidate_in_focus(candidate, focus_sections)]
    print(f"focus filtered candidates {len(candidates)} -> {len(filtered)} for {','.join(focus_sections)}", flush=True)
    return filtered


def build_focus_text(doc: Document, pages: list[DocumentPage], chunks: list[ContentChunk], focus_sections: list[str]) -> str:
    if not focus_sections:
        return ""
    return build_bundle_text(build_section_units(doc, pages, chunks, focus_sections))


def build_summary(args, doc, chunks, timings, artifacts, backends, pricing) -> dict[str, Any]:
    final, raw_entries, anchored, evidence_rejected, judge_input, anchor_rejected, judge_rejected, raw_extract, raw_judge = artifacts
    raw_count = len(raw_entries)
    anchor_rate = len(anchored) / raw_count * 100 if raw_count else 0.0
    judge_rate = len(final) / len(judge_input) * 100 if judge_input else 0.0
    extract_backend, judge_backend = backends
    extract_pricing, judge_pricing = pricing
    extract_cost = estimate_cost(raw_extract, extract_pricing)
    judge_cost = estimate_cost(raw_judge, judge_pricing)
    gates = build_gates(anchor_rate, judge_rate, final, timings, args)
    return {
        "run_id": make_focused_run_id(doc.file_name, parse_focus_sections(getattr(args, "focus_sections", None))),
        "standard_id": STANDARD_ID,
        "manual": doc.file_name,
        "doc_id": doc.doc_id,
        "architecture": "single-call full-book extraction + single-call batch judge + verbatim chunk anchoring",
        "focus_sections": parse_focus_sections(getattr(args, "focus_sections", None)),
        "manual_chunks": len(chunks),
        "manual_tokens_estimated": timings["manual_tokens_estimated"],
        "extract_backend": extract_backend.name,
        "extract_model": extract_backend.model,
        "judge_backend": judge_backend.name,
        "judge_model": judge_backend.model,
        "extract_usage": usage_tokens(raw_extract),
        "judge_usage": usage_tokens(raw_judge),
        "extract_cost_rmb": extract_cost,
        "judge_cost_rmb": judge_cost,
        "total_cost_rmb": extract_cost + judge_cost,
        "budget_rmb": args.budget_rmb,
        "raw_candidates": raw_count,
        "anchor_passed": len(anchored),
        "anchor_rejected": len(anchor_rejected),
        "weak_evidence_rejected": len(evidence_rejected),
        "judge_input": len(judge_input),
        "judge_accepted": len(final),
        "judge_rejected": len(judge_rejected),
        "judge_rejection_breakdown": dict(Counter(row.get("judge_category") or "other" for row in judge_rejected)),
        "final_by_type": dict(Counter(row["knowledge_object_type"] for row in final)),
        "l4_final": sum(1 for row in final if row.get("trust_level") == "L4"),
        "l3_final": sum(1 for row in final if row.get("trust_level") == "L3"),
        "timings": timings,
        "gates": gates,
    }


def build_gates(anchor_rate, judge_rate, final, timings, args) -> dict[str, dict[str, Any]]:
    l4_count = sum(1 for row in final if row.get("trust_level") == "L4")
    focus_sections = parse_focus_sections(getattr(args, "focus_sections", None))
    return {
        "G1": {"status": "PASS" if anchor_rate >= 80 else "FAIL", "value": anchor_rate, "requirement": "anchor_match_rate >= 80%"},
        "G2": {"status": "PASS" if judge_rate >= 50 else "FAIL", "value": judge_rate, "requirement": "judge_acceptance_rate >= 50%"},
        "G3": build_g3_gate(final, l4_count, focus_sections),
        "G4": {
            "status": "PASS" if timings["extract_seconds"] <= args.max_extract_seconds else "FAIL",
            "value": timings["extract_seconds"],
            "limit_seconds": args.max_extract_seconds,
            "requirement": "single full-book extraction completed within configured limit",
        },
    }


def build_g3_gate(final: list[dict[str, Any]], l4_count: int, focus_sections: list[str]) -> dict[str, Any]:
    if focus_sections:
        return {
            "status": "PASS" if len(final) > 0 else "FAIL",
            "value": len(final),
            "requirement": "focused section run produced at least one verified candidate",
        }
    return {"status": "PASS" if l4_count > 0 else "FAIL", "value": l4_count, "requirement": "L4 count > 0"}


def make_focused_run_id(file_name: str, focus_sections: list[str]) -> str:
    base = make_run_id(file_name).replace("_ashrae_g36", "_ashrae_g36_fullbook")
    if not focus_sections:
        return base
    suffix = "_".join(re.sub(r"[^a-zA-Z0-9]+", "_", section).strip("_") for section in focus_sections)
    return f"{base}_sections_{suffix}"


def build_report(summary: dict[str, Any], samples: dict[str, list[str]]) -> str:
    breakdown = ", ".join(f"{k}: {v}" for k, v in summary["judge_rejection_breakdown"].items()) or "none"
    by_type = ", ".join(f"{k}: {v}" for k, v in summary["final_by_type"].items()) or "none"
    gates = summary["gates"]
    return f"""# ASHRAE Guideline 36 Full-Book Run Report

**Run ID:** {summary["run_id"]}
**Standard:** {summary["standard_id"]}
**Document:** {summary["manual"]}
**Architecture:** {summary["architecture"]}
**Focus sections:** {", ".join(summary["focus_sections"]) or "all"}
**Extract backend:** {summary["extract_backend"]} / {summary["extract_model"]}
**Judge backend:** {summary["judge_backend"]} / {summary["judge_model"]}

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | {summary["manual_chunks"]} |
| Manual tokens estimated | {summary["manual_tokens_estimated"]} |
| Extract calls | {summary["extract_usage"]["request_count"]} |
| Extract input tokens | {summary["extract_usage"]["prompt_tokens"]} |
| Extract output tokens | {summary["extract_usage"]["completion_tokens"]} |
| Judge calls | {summary["judge_usage"]["request_count"]} |
| Judge total tokens | {summary["judge_usage"]["total_tokens"]} |
| Total cost | ¥{summary["total_cost_rmb"]:.4f} / ¥{summary["budget_rmb"]:.2f} |
| Extract wallclock | {summary["timings"]["extract_seconds"]:.2f}s |
| Total wallclock | {summary["timings"]["total_seconds"]:.2f}s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | {summary["raw_candidates"]} |
| Anchor passed | {summary["anchor_passed"]} |
| Anchor rejected | {summary["anchor_rejected"]} |
| Weak evidence rejected before judge | {summary["weak_evidence_rejected"]} |
| Judge input | {summary["judge_input"]} |
| Judge accepted | {summary["judge_accepted"]} |
| Judge rejected | {summary["judge_rejected"]} |
| Judge rejection breakdown | {breakdown} |
| Final by type | {by_type} |
| L4 / L3 | {summary["l4_final"]} / {summary["l3_final"]} |

## Samples

### Accepted
{chr(10).join(samples["accepted"]) or "None"}

### Anchor Rejected
{chr(10).join(samples["anchor_rejected"]) or "None"}

### Judge Rejected
{chr(10).join(samples["judge_rejected"]) or "None"}

## Stability Gates

- G1 anchor_match_rate >= 80%: {gates["G1"]["status"]} ({gates["G1"]["value"]:.1f}%)
- G2 judge_acceptance_rate >= 50%: {gates["G2"]["status"]} ({gates["G2"]["value"]:.1f}%)
- G3 {gates["G3"]["requirement"]}: {gates["G3"]["status"]} ({gates["G3"]["value"]})
- G4 extract wallclock <= configured limit: {gates["G4"]["status"]} ({gates["G4"]["value"]:.2f}s / {gates["G4"]["limit_seconds"]:.0f}s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
"""


def write_outputs(args, summary: dict[str, Any], full_book_text: str, artifacts: tuple[Any, ...]) -> None:
    final, raw_entries, anchored, evidence_rejected, judge_input, anchor_rejected, judge_rejected, raw_extract, raw_judge = artifacts
    output_dir = Path(args.output_dir) / summary["run_id"]
    output_dir.mkdir(parents=True, exist_ok=False)
    write_jsonl(output_dir / "candidates_llm_raw.jsonl", raw_entries)
    write_jsonl(output_dir / "candidates_llm_anchor_passed.jsonl", anchored)
    write_jsonl(output_dir / "candidates_llm_evidence_passed.jsonl", judge_input)
    write_jsonl(output_dir / "candidates_llm_verified.jsonl", final)
    write_jsonl(output_dir / "candidates_llm_rejected.jsonl", anchor_rejected + evidence_rejected)
    write_jsonl(output_dir / "candidates_llm_judge_rejected.jsonl", judge_rejected)
    write_jsonl(output_dir / "raw_extract_response.jsonl", raw_extract)
    write_jsonl(output_dir / "raw_judge_responses.jsonl", raw_judge)
    (output_dir / "full_book_manifest.json").write_text(json.dumps(full_book_manifest(full_book_text), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    samples = build_samples(final, anchor_rejected + evidence_rejected, judge_rejected)
    (output_dir / "REPORT.md").write_text(build_report(summary, samples), encoding="utf-8")
    summary["output_dir"] = str(output_dir)
    summary["report_path"] = str(output_dir / "REPORT.md")
    (output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def full_book_manifest(full_book_text: str) -> dict[str, Any]:
    return {
        "text_chars": len(full_book_text),
        "text_sha1": sha1_text(full_book_text),
        "tokens_estimated": estimate_tokens(full_book_text),
        "note": "Full ASHRAE text is intentionally not persisted; only hash/size metadata is stored.",
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    start = time.monotonic()
    extract_backend, extract_pricing = load_backend(args.extract_backend)
    judge_backend, judge_pricing = load_backend(args.judge_backend)
    if extract_backend.name == judge_backend.name:
        raise ValueError("extract and judge backends must be different")
    extract_backend = backend_with_overrides(
        extract_backend,
        max_tokens=args.extract_max_tokens,
        timeout_seconds=args.extract_timeout_seconds,
    )
    judge_backend = backend_with_overrides(
        judge_backend,
        max_tokens=args.judge_max_tokens,
        timeout_seconds=args.judge_timeout_seconds,
    )
    doc, pages, chunks = load_document_rows(args.doc_id)
    validate_official_ashrae_doc(doc, pages)
    full_book_text = assemble_full_book_text(chunks)
    token_estimate = estimate_tokens(full_book_text)
    print(f"manual chunks={len(chunks)} tokens~{token_estimate}", flush=True)
    if token_estimate > args.context_token_cap:
        raise ValueError(f"Full-book text exceeds context cap: {token_estimate} > {args.context_token_cap}")
    raw_extract: list[dict[str, Any]] = []
    extract_start = time.monotonic()
    focus_sections = parse_focus_sections(args.focus_sections)
    focus_text = build_focus_text(doc, pages, chunks, focus_sections)
    extracted = extract_full_book(
        doc,
        full_book_text,
        extract_backend,
        raw_extract,
        target_candidates=args.target_candidates,
        focus_sections=focus_sections,
        focus_text=focus_text,
    )
    extracted = filter_candidates_by_focus(extracted, focus_sections)
    if len(extracted) > args.max_raw_candidates:
        print(f"truncating raw candidates {len(extracted)} -> {args.max_raw_candidates}", flush=True)
        extracted = extracted[: args.max_raw_candidates]
    extract_seconds = time.monotonic() - extract_start
    raw_entries = build_raw_entries(extracted, doc, extract_backend)
    print(f"anchoring {len(raw_entries)} raw candidates", flush=True)
    anchored, anchor_rejected = anchor_candidates(raw_entries, chunks)
    judge_input, evidence_rejected = filter_weak_evidence_candidates(anchored)
    print(f"weak_evidence_rejected={len(evidence_rejected)} judge_input={len(judge_input)}", flush=True)
    accepted, judge_rejected, raw_judge = judge_candidates_batch(judge_input, judge_backend)
    final = dedup_candidates(accepted)
    timings = {
        "manual_tokens_estimated": token_estimate,
        "extract_seconds": extract_seconds,
        "total_seconds": time.monotonic() - start,
    }
    artifacts = (final, raw_entries, anchored, evidence_rejected, judge_input, anchor_rejected, judge_rejected, raw_extract, raw_judge)
    summary = build_summary(args, doc, chunks, timings, artifacts, (extract_backend, judge_backend), (extract_pricing, judge_pricing))
    write_outputs(args, summary, full_book_text, artifacts)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doc-id", required=True)
    parser.add_argument("--extract-backend", required=True)
    parser.add_argument("--judge-backend", required=True)
    parser.add_argument("--output-dir", default="output/ashrae_guideline36_fullbook")
    parser.add_argument("--budget-rmb", type=float, default=30.0)
    parser.add_argument("--context-token-cap", type=int, default=850_000)
    parser.add_argument("--extract-max-tokens", type=int, default=120_000)
    parser.add_argument("--judge-max-tokens", type=int, default=80_000)
    parser.add_argument("--extract-timeout-seconds", type=int, default=900)
    parser.add_argument("--judge-timeout-seconds", type=int, default=900)
    parser.add_argument("--max-extract-seconds", type=float, default=600.0)
    parser.add_argument("--target-candidates", type=int, default=100)
    parser.add_argument("--max-raw-candidates", type=int, default=150)
    parser.add_argument("--focus-sections", default="", help="Comma-separated sections to extract while using full-book context, e.g. 5.20,5.21")
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
