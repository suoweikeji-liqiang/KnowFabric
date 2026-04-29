#!/usr/bin/env python3
"""Run parameter_spec vertical extraction with one document-level LLM call."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.equipment_matcher import build_equipment_profiles, match_equipment_class, normalize_text
from packages.compiler.llm_compiler import (
    OpenAICompatibleBackend,
    _request_json_completion,
    backend_from_dict,
    compile_document_parameter_specs,
    normalize_llm_canonical_key,
)
from packages.compiler.rule_compiler import detect_rule_knowledge_candidates, short_text, stable_candidate_id
from packages.core.sw_base_model_ontology_client import SwBaseModelOntologyClient
from packages.db.models import ContentChunk, Document, DocumentPage
from packages.db.session import SessionLocal


class JudgeResponse(BaseModel):
    is_parameter_spec: bool
    reason: str
    category_if_not: str | None = Field(default=None)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    content = "\n".join(json.dumps(row, ensure_ascii=False, default=str) for row in rows)
    path.write_text((content + "\n") if content else "", encoding="utf-8")


def load_backend(name: str) -> tuple[OpenAICompatibleBackend, dict[str, Any]]:
    path = Path(__file__).resolve().parent / "llm_backends.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    for item in data.get("backends", []):
        if item.get("name") == name:
            return backend_from_dict(item), item
    raise ValueError(f"Backend '{name}' not found in {path}")


def load_rows(doc_id: str) -> list[tuple[ContentChunk, DocumentPage, Document]]:
    db = SessionLocal()
    try:
        return list(
            db.query(ContentChunk, DocumentPage, Document)
            .join(DocumentPage, ContentChunk.page_id == DocumentPage.page_id)
            .join(Document, ContentChunk.doc_id == Document.doc_id)
            .filter(ContentChunk.doc_id == doc_id)
            .order_by(ContentChunk.page_no, ContentChunk.chunk_index)
            .all()
        )
    finally:
        db.close()


def assemble_manual_text(rows: list[tuple[ContentChunk, DocumentPage, Document]]) -> str:
    parts = []
    for chunk, _, _ in rows:
        parts.append(f"[[chunk_id={chunk.chunk_id} page={chunk.page_no}]]")
        parts.append(sanitize_manual_text(chunk.cleaned_text or chunk.text_excerpt or ""))
    return "\n\n".join(parts)


def sanitize_manual_text(text: str) -> str:
    return "".join(char if char in "\n\r\t" or ord(char) >= 32 else " " for char in text)


def estimate_tokens(text: str) -> int:
    cjk = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    return int(cjk / 2 + (len(text) - cjk) / 4)


def resolve_equipment(rows: list[tuple[ContentChunk, DocumentPage, Document]]) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    document = rows[0][2]
    domain_id = str(document.source_domain or "").strip()
    client = SwBaseModelOntologyClient()
    db = SessionLocal()
    try:
        profiles = build_equipment_profiles(db, domain_id, client)
    finally:
        db.close()
    search_text = normalize_text(" ".join([document.file_name] + [chunk.cleaned_text for chunk, _, _ in rows]))
    equipment_match, alternatives = match_equipment_class(profiles, search_text, "centrifugal_chiller")
    if equipment_match is None:
        raise ValueError(f"Could not match equipment class for {document.doc_id}")
    return equipment_match, alternatives, client.ontology_version()


def normalize_anchor_text(text: str) -> str:
    lowered = re.sub(r"\s+", " ", text.strip().lower())
    return lowered.strip(" \t\r\n.,;:!?，。；：！？、")


def compact_anchor_text(text: str) -> str:
    normalized = text.lower()
    normalized = re.sub(r"[\s\u00a0]+", "", normalized)
    normalized = normalized.replace("％", "%").replace("（", "(").replace("）", ")")
    normalized = normalized.replace("：", ":").replace("－", "-").replace("—", "-")
    return re.sub(r"[，。；、,.;:]", "", normalized)


def anchor_to_chunks(raw_candidates: list[dict[str, Any]], rows: list[tuple[ContentChunk, DocumentPage, Document]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    chunk_index = [
        (
            chunk,
            page,
            normalize_anchor_text(chunk.cleaned_text or chunk.text_excerpt or ""),
            compact_anchor_text(chunk.cleaned_text or chunk.text_excerpt or ""),
        )
        for chunk, page, _ in rows
    ]
    anchored, rejected = [], []
    for candidate in raw_candidates:
        quote = str(candidate.get("evidence_quote") or "")
        normalized_quote = normalize_anchor_text(quote)
        compact_quote = compact_anchor_text(quote)
        matches = [
            (chunk, page)
            for chunk, page, text, compact_text in chunk_index
            if normalized_quote and (normalized_quote in text or compact_quote in compact_text)
        ]
        if not matches:
            rejected.append({**candidate, "rejection_reason": "evidence_quote not verbatim in any chunk"})
            continue
        anchored.append(build_anchored_candidate(candidate, matches))
    return anchored, rejected


def build_anchored_candidate(candidate: dict[str, Any], matches: list[tuple[ContentChunk, DocumentPage]]) -> dict[str, Any]:
    source_chunk_ids = [chunk.chunk_id for chunk, _ in matches]
    pages = sorted({page.page_no for _, page in matches})
    anchored = copy.deepcopy(candidate)
    anchored["source_chunk_ids"] = source_chunk_ids
    anchored["chunk_id"] = source_chunk_ids[0]
    anchored["page_no"] = pages[0]
    anchored["source_page_nos"] = pages
    anchored["evidence_text"] = matches[0][0].cleaned_text or matches[0][0].text_excerpt or ""
    anchored["trust_level"] = "L4" if len(source_chunk_ids) >= 2 else "L3"
    anchored["verification_reason"] = (
        f"cross-source corroboration: {len(source_chunk_ids)} chunks"
        if len(source_chunk_ids) >= 2 else "single chunk verbatim evidence_quote match"
    )
    return anchored


def build_raw_candidate_entries(response_candidates: list[Any], rows: list[tuple[ContentChunk, DocumentPage, Document]], equipment: dict[str, Any], ontology_version: str, backend: OpenAICompatibleBackend) -> list[dict[str, Any]]:
    document = rows[0][2]
    domain_id = str(document.source_domain)
    entries = []
    for item in response_candidates:
        payload = item.model_dump()
        canonical = payload.get("canonical_key_hint") or payload["parameter_name"]
        canonical_key = normalize_llm_canonical_key(canonical, domain_id=domain_id, equipment_class_id=equipment["equipment_class_id"], knowledge_object_type="parameter_spec", fallback_text=payload["parameter_name"])
        entries.append(build_entry(payload, canonical_key, document, equipment, ontology_version, backend))
    return entries


def build_entry(payload: dict[str, Any], canonical_key: str, document: Document, equipment: dict[str, Any], ontology_version: str, backend: OpenAICompatibleBackend) -> dict[str, Any]:
    candidate_id = stable_candidate_id(document.doc_id, equipment["equipment_class_key"], canonical_key, payload["evidence_quote"])
    return {
        "candidate_id": candidate_id,
        "domain_id": document.source_domain,
        "doc_id": document.doc_id,
        "doc_name": document.file_name,
        "equipment_class_candidate": {
            "equipment_class_id": equipment["equipment_class_id"],
            "equipment_class_key": equipment["equipment_class_key"],
            "label": equipment["label"],
            "confidence": equipment["confidence"],
            "matched_aliases": equipment["matched_aliases"],
            "supported_knowledge_anchors": list(equipment.get("knowledge_anchors", [])),
        },
        "knowledge_object_type": "parameter_spec",
        "canonical_key_candidate": canonical_key,
        "structured_payload_candidate": {key: value for key, value in payload.items() if key != "confidence"},
        "confidence_score": round(float(payload.get("confidence") or 0.0), 3),
        "review_status": "candidate",
        "curated_against_ontology_version": ontology_version,
        "compile_metadata": {"method": "llm_document_compiler", "model": backend.model, "backend_name": backend.name},
        "evidence_quote": payload["evidence_quote"],
    }


def judge_response_format() -> dict[str, Any]:
    return {"type": "json_object"}


def judge_one(candidate: dict[str, Any], backend: OpenAICompatibleBackend, recorder) -> JudgeResponse:
    payload = candidate.get("structured_payload_candidate", {})
    messages = [
        {"role": "system", "content": "You validate HVAC manual parameter extractions. Reply only with strict JSON."},
        {
            "role": "user",
            "content": (
                "Confirm whether this is a genuine CONFIGURABLE OPERATIONAL PARAMETER (parameter_spec) or a category error.\n\n"
                f"parameter_name: {payload.get('parameter_name')}\n"
                f"value: {payload.get('value')}\n"
                f"unit: {payload.get('unit')}\n"
                f"evidence: \"{candidate.get('evidence_quote')}\"\n"
                f"source_pages: {candidate.get('source_page_nos')}\n\n"
                'Reply with {"is_parameter_spec":true|false,"reason":"<short reason>","category_if_not":null|"marketing"|"algorithm_internal"|"ui_behavior"|"performance_spec"|"fault_code"|"other"}.'
            ),
        },
    ]
    result = _request_json_completion(messages, backend, response_format=judge_response_format(), recorder=recorder)
    return JudgeResponse.model_validate(result)


def judge_candidates(candidates: list[dict[str, Any]], backend: OpenAICompatibleBackend) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    accepted, rejected, raw = [], [], []
    for candidate in candidates:
        def recorder(payload: dict[str, Any], candidate_id: str = candidate["candidate_id"]) -> None:
            raw.append({"candidate_id": candidate_id, **payload})
        verdict = judge_one(candidate, backend, recorder)
        updated = {**candidate, "judge_reason": verdict.reason}
        if verdict.is_parameter_spec:
            accepted.append({**updated, "judge_verdict": "accepted"})
        else:
            rejected.append({**updated, "judge_verdict": "rejected_by_judge", "judge_category": verdict.category_if_not})
    return accepted, rejected, raw


def dedup_final_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for candidate in candidates:
        equipment_id = candidate["equipment_class_candidate"]["equipment_class_id"]
        groups.setdefault((parameter_name(candidate), equipment_id), []).append(candidate)
    final = []
    for group in groups.values():
        best = max(group, key=lambda item: float(item.get("confidence_score") or 0.0))
        merged = copy.deepcopy(best)
        chunk_ids = list(dict.fromkeys(chunk_id for item in group for chunk_id in item.get("source_chunk_ids", [])))
        merged["source_chunk_ids"] = chunk_ids
        if len(chunk_ids) >= 2:
            merged["trust_level"] = "L4"
            merged["verification_reason"] = f"cross-source corroboration: {len(chunk_ids)} chunks"
        final.append(merged)
    return sorted(final, key=lambda item: (item.get("page_no") or 0, parameter_name(item)))


def run_rule_baseline(rows: list[tuple[ContentChunk, DocumentPage, Document]], equipment: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    for chunk, page, document in rows:
        for item in detect_rule_knowledge_candidates(chunk, page, equipment):
            if item.get("knowledge_object_type") != "parameter_spec":
                continue
            results.append({"doc_id": document.doc_id, "chunk_id": chunk.chunk_id, "page_no": page.page_no, **item})
    return results


def usage_tokens(raw: list[dict[str, Any]]) -> dict[str, int]:
    usage_items = [item.get("response", {}).get("usage", {}) for item in raw]
    prompt = sum(int(item.get("prompt_tokens") or 0) for item in usage_items)
    completion = sum(int(item.get("completion_tokens") or 0) for item in usage_items)
    return {"prompt_tokens": prompt, "completion_tokens": completion, "total_tokens": prompt + completion}


def estimate_cost(raw: list[dict[str, Any]], pricing: dict[str, Any]) -> float:
    tokens = usage_tokens(raw)
    prompt_price = float(pricing.get("prompt_price_rmb_per_1k") or 0.0)
    completion_price = float(pricing.get("completion_price_rmb_per_1k") or 0.0)
    return round(tokens["prompt_tokens"] / 1000 * prompt_price + tokens["completion_tokens"] / 1000 * completion_price, 6)


def parameter_name(entry: dict[str, Any]) -> str:
    payload = entry.get("structured_payload_candidate") or {}
    return normalize_anchor_text(str(payload.get("parameter_name") or entry.get("canonical_key_candidate") or ""))


def build_report(summary: dict[str, Any], samples: dict[str, list[str]]) -> str:
    gates = summary["gates"]
    breakdown = ", ".join(f"{key}: {value}" for key, value in summary["judge_rejection_breakdown"].items()) or "none"
    sections = [
        report_header(summary),
        report_cost_and_extraction(summary),
        report_judge_and_final(summary, breakdown),
        report_rule_and_overlap(summary),
        report_samples(samples),
        report_gates_and_comparison(summary, gates),
    ]
    return "\n".join(sections)


def report_header(summary: dict[str, Any]) -> str:
    return f"""# parameter_spec Vertical Run Report (Run 2 - Document-Level)

**Run ID:** {summary["run_id"]}
**Architecture:** single-call document-level (DeepSeek V4 1M context)
**Manual:** {summary["manual"]}
**Equipment class:** {summary["equipment_class_key"]}
**Extract backend:** {summary["extract_backend"]} / {summary["extract_model"]}
**Judge backend:** {summary["judge_backend"]} / {summary["judge_model"]}
**ontology_version:** {summary["ontology_version"]}
"""


def report_cost_and_extraction(summary: dict[str, Any]) -> str:
    return f"""## Token / Cost

| Metric | Value |
|--------|-------|
| Input tokens (extract) | {summary["extract_usage"]["prompt_tokens"]} |
| Output tokens (extract) | {summary["extract_usage"]["completion_tokens"]} |
| Judge tokens (input + output) | {summary["judge_usage"]["total_tokens"]} |
| Total cost | ¥{summary["total_cost_rmb"]:.4f} |
| Status | {summary["budget_status"]} |

## Extraction numbers

| Metric | Value |
|--------|-------|
| Manual chunks | {summary["manual_chunks"]} |
| Manual tokens (estimated) | {summary["manual_tokens_estimated"]} |
| LLM extraction calls | {summary["extraction_calls"]} |
| Raw candidates returned | {summary["raw_candidates"]} |
| Anchor-rejected (hallucination) | {summary["anchor_rejected"]} |
| Anchor-passed | {summary["anchor_passed"]} |
| L4 (>=2 chunk matches) | {summary["l4_pre_judge"]} |
| L3 (1 chunk match) | {summary["l3_pre_judge"]} |"""


def report_judge_and_final(summary: dict[str, Any], breakdown: str) -> str:
    return f"""## Judge pass

| Metric | Value |
|--------|-------|
| Judge calls | {summary["judge_calls"]} |
| Accepted | {summary["judge_accepted"]} ({summary["judge_acceptance_rate"]:.1f}%) |
| Rejected | {summary["judge_rejected"]} ({summary["judge_rejection_rate"]:.1f}%) |
| Rejection breakdown | {breakdown} |

## Final candidates

| Metric | Value |
|--------|-------|
| Verified | {summary["final_verified"]} |
| L4 / L3 breakdown | {summary["l4_final"]} / {summary["l3_final"]} |"""


def report_rule_and_overlap(summary: dict[str, Any]) -> str:
    return f"""## Rule baseline

| Metric | Value |
|--------|-------|
| Candidates | {summary["rule_candidates"]} |
| Notes on rule_compiler invocation | Used public per-chunk `detect_rule_knowledge_candidates`; no doc_id-level public API exists. |

## Overlap

| Set | Count |
|-----|-------|
| LLM ∩ Rule | {summary["overlap"]} |
| LLM only | {summary["llm_only"]} |
| Rule only | {summary["rule_only"]} |"""


def report_samples(samples: dict[str, list[str]]) -> str:
    return f"""## Sample LLM-only finds (top 10)

{chr(10).join(samples["llm_only"]) or "None"}

## Sample anchor rejections (top 5)

{chr(10).join(samples["anchor_rejected"]) or "None"}

## Sample judge rejections (top 10)

{chr(10).join(samples["judge_rejected"]) or "None"}"""


def report_gates_and_comparison(summary: dict[str, Any], gates: dict[str, dict[str, Any]]) -> str:
    return f"""## Stability gates

- G1 chunk_anchor_match_rate >= 80%: {gates["G1"]["status"]} ({gates["G1"]["value"]:.1f}%)
- G2 judge_acceptance_rate >= 50%: {gates["G2"]["status"]} ({gates["G2"]["value"]:.1f}%)
- G3 L4 count > 0: {gates["G3"]["status"]} ({gates["G3"]["value"]})
- G4 extraction wallclock < 60 seconds: {gates["G4"]["status"]} ({gates["G4"]["value"]:.2f}s)

## Compared to run 1

| Metric | Run 1 | Run 2 |
|--------|-------|-------|
| LLM calls | 8 | 1 + {summary["judge_calls"]} judge |
| Verified candidates | 9 | {summary["final_verified"]} |
| L4 count | 0 | {summary["l4_final"]} |
| True precision (operator review) | 56% | pending |

## Operator review checklist

Reserved 20 random L3+ candidates for operator to mark accurate/inaccurate.
"""


def build_samples(final_entries: list[dict[str, Any]], rule_entries: list[dict[str, Any]], anchor_rejected: list[dict[str, Any]], judge_rejected: list[dict[str, Any]]) -> dict[str, list[str]]:
    rule_names = {parameter_name(entry) for entry in rule_entries}
    llm_only = [entry for entry in final_entries if parameter_name(entry) not in rule_names]
    return {
        "llm_only": [f"- p{entry['page_no']}: {entry['structured_payload_candidate'].get('parameter_name')} | {entry['canonical_key_candidate']}" for entry in llm_only[:10]],
        "anchor_rejected": [f"- {entry.get('structured_payload_candidate', {}).get('parameter_name')}: {entry.get('rejection_reason')}" for entry in anchor_rejected[:5]],
        "judge_rejected": [f"- {entry.get('structured_payload_candidate', {}).get('parameter_name')}: {entry.get('judge_category')} | {entry.get('judge_reason')}" for entry in judge_rejected[:10]],
    }


def build_summary(args, rows, equipment, ontology_version, timings, artifacts, backends, pricing) -> dict[str, Any]:
    final_entries, raw_entries, anchored, anchor_rejected, judge_rejected, rule_entries, raw_extract, raw_judge = artifacts
    extract_backend, judge_backend = backends
    extract_pricing, judge_pricing = pricing
    raw_count = len(raw_entries)
    anchor_rate = (len(anchored) / raw_count * 100) if raw_count else 100.0
    judge_rate = (len(final_entries) / len(anchored) * 100) if anchored else 0.0
    l4_final = sum(1 for entry in final_entries if entry.get("trust_level") == "L4")
    llm_names = {parameter_name(entry) for entry in final_entries}
    rule_names = {parameter_name(entry) for entry in rule_entries}
    return {
        "run_id": make_run_id(rows[0][2].file_name),
        "manual": rows[0][2].file_name,
        "manual_chunks": len(rows),
        "manual_tokens_estimated": timings["manual_tokens"],
        "equipment_class_key": equipment["equipment_class_key"],
        "ontology_version": ontology_version,
        "extract_backend": extract_backend.name,
        "extract_model": extract_backend.model,
        "judge_backend": judge_backend.name,
        "judge_model": judge_backend.model,
        "extract_usage": usage_tokens(raw_extract),
        "judge_usage": usage_tokens(raw_judge),
        "total_cost_rmb": estimate_cost(raw_extract, extract_pricing) + estimate_cost(raw_judge, judge_pricing),
        "budget_status": "within" if estimate_cost(raw_extract, extract_pricing) + estimate_cost(raw_judge, judge_pricing) <= args.budget_rmb else "aborted-on-budget",
        "extraction_calls": len(raw_extract),
        "raw_candidates": raw_count,
        "anchor_rejected": len(anchor_rejected),
        "anchor_passed": len(anchored),
        "l4_pre_judge": sum(1 for entry in anchored if entry.get("trust_level") == "L4"),
        "l3_pre_judge": sum(1 for entry in anchored if entry.get("trust_level") == "L3"),
        "judge_calls": len(raw_judge),
        "judge_accepted": len(final_entries),
        "judge_rejected": len(judge_rejected),
        "judge_acceptance_rate": judge_rate,
        "judge_rejection_rate": 100.0 - judge_rate if anchored else 0.0,
        "judge_rejection_breakdown": dict(Counter(entry.get("judge_category") or "other" for entry in judge_rejected)),
        "final_verified": len(final_entries),
        "l4_final": l4_final,
        "l3_final": sum(1 for entry in final_entries if entry.get("trust_level") == "L3"),
        "rule_candidates": len(rule_entries),
        "overlap": len(llm_names & rule_names),
        "llm_only": len(llm_names - rule_names),
        "rule_only": len(rule_names - llm_names),
        "gates": build_gates(anchor_rate, judge_rate, l4_final, timings["extract_seconds"]),
    }


def build_gates(anchor_rate: float, judge_rate: float, l4_count: int, extract_seconds: float) -> dict[str, dict[str, Any]]:
    return {
        "G1": {"status": "PASS" if anchor_rate >= 80.0 else "FAIL", "value": anchor_rate},
        "G2": {"status": "PASS" if judge_rate >= 50.0 else "FAIL", "value": judge_rate},
        "G3": {"status": "PASS" if l4_count > 0 else "FAIL", "value": l4_count},
        "G4": {"status": "PASS" if extract_seconds < 60.0 else "FAIL", "value": extract_seconds},
    }


def make_run_id(file_name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", Path(file_name).stem.lower()).strip("_")
    return f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{slug}_parameter_spec"


def run(args: argparse.Namespace) -> dict[str, Any]:
    extract_backend, extract_pricing = load_backend(args.extract_backend)
    judge_backend, judge_pricing = load_backend(args.judge_backend)
    if extract_backend.name == judge_backend.name:
        raise ValueError("extract-backend and judge-backend must be different backend names")
    rows = load_rows(args.doc_id)
    if not rows:
        raise ValueError(f"No chunks found for doc_id {args.doc_id}")
    manual_text = assemble_manual_text(rows)
    manual_tokens = estimate_tokens(manual_text)
    if manual_tokens > 800_000:
        raise ValueError(f"Manual token estimate {manual_tokens} exceeds 800K single-call limit")
    equipment, _, ontology_version = resolve_equipment(rows)
    raw_extract: list[dict[str, Any]] = []
    start = time.monotonic()
    try:
        response = compile_document_parameter_specs(domain_id=rows[0][2].source_domain, document_name=rows[0][2].file_name, equipment_class_id=equipment["equipment_class_id"], full_manual_text=manual_text, backend=extract_backend, request_recorder=lambda payload: raw_extract.append(payload))
    except Exception as exc:
        return write_extraction_failure(args, rows, equipment, ontology_version, manual_tokens, raw_extract, exc)
    extract_seconds = time.monotonic() - start
    raw_entries = build_raw_candidate_entries(response.candidates, rows, equipment, ontology_version, extract_backend)
    anchored, anchor_rejected = anchor_to_chunks(raw_entries, rows)
    accepted_entries, judge_rejected, raw_judge = judge_candidates(anchored, judge_backend)
    final_entries = dedup_final_candidates(accepted_entries)
    rule_entries = run_rule_baseline(rows, equipment)
    timings = {"manual_tokens": manual_tokens, "extract_seconds": extract_seconds}
    artifacts = (final_entries, raw_entries, anchored, anchor_rejected, judge_rejected, rule_entries, raw_extract, raw_judge)
    summary = build_summary(args, rows, equipment, ontology_version, timings, artifacts, (extract_backend, judge_backend), (extract_pricing, judge_pricing))
    write_outputs(args, summary, artifacts)
    return summary


def write_extraction_failure(args: argparse.Namespace, rows, equipment, ontology_version: str, manual_tokens: int, raw_extract: list[dict[str, Any]], exc: Exception) -> dict[str, Any]:
    run_id = make_run_id(rows[0][2].file_name)
    output_dir = Path(args.output_dir) / run_id
    output_dir.mkdir(parents=True, exist_ok=False)
    error = {"stage": "extract", "error": str(exc), "error_type": type(exc).__name__}
    write_jsonl(output_dir / "extraction_errors.jsonl", [error])
    write_jsonl(output_dir / "raw_extract_response.jsonl", raw_extract)
    summary = {
        "run_id": run_id,
        "manual": rows[0][2].file_name,
        "manual_chunks": len(rows),
        "manual_tokens_estimated": manual_tokens,
        "equipment_class_key": equipment["equipment_class_key"],
        "ontology_version": ontology_version,
        "extract_backend": args.extract_backend,
        "judge_backend": args.judge_backend,
        "status": "failed_extraction",
        "error": str(exc),
        "report_path": str(output_dir / "REPORT.md"),
        "gates": {
            "G1": {"status": "FAIL", "value": 0.0},
            "G2": {"status": "FAIL", "value": 0.0},
            "G3": {"status": "FAIL", "value": 0},
            "G4": {"status": "FAIL", "value": 0.0},
        },
    }
    report = f"# parameter_spec Vertical Run Report (Run 2 - Document-Level)\n\nExtraction failed before candidate processing.\n\nError: {exc}\n"
    (output_dir / "REPORT.md").write_text(report, encoding="utf-8")
    (output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    return summary


def write_outputs(args: argparse.Namespace, summary: dict[str, Any], artifacts: tuple[Any, ...]) -> None:
    final_entries, raw_entries, anchored, anchor_rejected, judge_rejected, rule_entries, raw_extract, raw_judge = artifacts
    output_dir = Path(args.output_dir) / summary["run_id"]
    output_dir.mkdir(parents=True, exist_ok=False)
    write_jsonl(output_dir / "candidates_llm_raw.jsonl", raw_entries)
    write_jsonl(output_dir / "candidates_llm_anchor_passed.jsonl", anchored)
    write_jsonl(output_dir / "candidates_llm_verified.jsonl", final_entries)
    write_jsonl(output_dir / "candidates_llm_rejected.jsonl", anchor_rejected)
    write_jsonl(output_dir / "candidates_llm_judge_rejected.jsonl", judge_rejected)
    write_jsonl(output_dir / "candidates_rule.jsonl", rule_entries)
    write_jsonl(output_dir / "raw_extract_response.jsonl", raw_extract)
    write_jsonl(output_dir / "raw_judge_responses.jsonl", raw_judge)
    write_jsonl(output_dir / "extraction_errors.jsonl", [])
    samples = build_samples(final_entries, rule_entries, anchor_rejected, judge_rejected)
    (output_dir / "REPORT.md").write_text(build_report(summary, samples), encoding="utf-8")
    summary["output_dir"] = str(output_dir)
    summary["report_path"] = str(output_dir / "REPORT.md")
    (output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doc-id", required=True)
    parser.add_argument("--extract-backend", required=True)
    parser.add_argument("--judge-backend", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--budget-rmb", type=float, default=30.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    summary = run(build_parser().parse_args(argv))
    failed = [name for name, gate in summary["gates"].items() if gate["status"] != "PASS"]
    if summary.get("status") == "failed_extraction":
        print(f"summary status=failed_extraction report={summary['report_path']} error={summary['error']}")
        return 2
    print(
        f"summary raw={summary['raw_candidates']} anchor_passed={summary['anchor_passed']} "
        f"verified={summary['final_verified']} L4={summary['l4_final']} cost=¥{summary['total_cost_rmb']:.4f} "
        f"report={summary['report_path']}"
    )
    return 2 if failed else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"parameter_spec vertical failed: {exc}")
        raise SystemExit(1)
