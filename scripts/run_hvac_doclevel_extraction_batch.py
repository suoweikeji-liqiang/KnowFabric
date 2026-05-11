#!/usr/bin/env python3
"""Compare document-level HVAC knowledge extraction backends over a source manifest."""

from __future__ import annotations

import argparse
import copy
import contextlib
import http.client
import json
import re
import signal
import sys
import time
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.equipment_matcher import build_equipment_profiles, match_equipment_class, normalize_text
from packages.compiler.llm_compiler import (
    OpenAICompatibleBackend,
    _request_json_completion,
    repair_json_response_with_backend,
    response_content_text,
)
from packages.compiler.rule_compiler import stable_candidate_id
from packages.core.config import settings
from packages.core.sw_base_model_ontology_client import SwBaseModelOntologyClient
from packages.db.models import ContentChunk, Document, DocumentPage
from packages.db.session import SessionLocal
from packages.storage.manager import StorageManager
from scripts.build_review_packs_from_candidates import write_review_packs_from_candidate_file
from scripts.bootstrap_review_packs_batch import bootstrap_review_pack_directory
from scripts.check_review_pack_readiness import check_review_pack_directory
from scripts.llm_backend_config import load_backend
from scripts.run_hvac_source_batch import SourceItem, ensure_document_imported, ensure_parsed_and_chunked, load_manifest, select_items


SUPPORTED_TYPES = (
    "fault_code",
    "parameter_spec",
    "performance_spec",
    "maintenance_procedure",
    "application_guidance",
    "operational_sequence",
    "fault_diagnostic_rule",
    "diagnostic_step",
    "symptom",
)


class HvacDocCandidate(BaseModel):
    knowledge_type: str
    title: str
    canonical_key_hint: str | None = None
    summary: str
    structured_payload: dict[str, Any] | None = Field(default_factory=dict)
    evidence_quote: str
    page_hint: int | None = None
    confidence: float = Field(ge=0.0, le=1.0)


class HvacDocExtractionResponse(BaseModel):
    candidates: list[HvacDocCandidate] = Field(default_factory=list)
    skipped_reason: str | None = None


class HvacJudgeVerdict(BaseModel):
    candidate_id: str
    is_valid_hvac_knowledge: bool
    reason: str
    category_if_not: str | None = None


class HvacJudgeResponse(BaseModel):
    verdicts: list[HvacJudgeVerdict] = Field(default_factory=list)


@contextlib.contextmanager
def wall_clock_timeout(seconds: int, *, label: str) -> None:
    """Abort one long-running backend call after a hard wall-clock deadline."""

    if seconds <= 0:
        yield
        return

    def _raise_timeout(signum, frame):  # noqa: ANN001, ARG001
        raise TimeoutError(f"{label} exceeded wall-clock timeout of {seconds} seconds")

    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, 0)
    signal.signal(signal.SIGALRM, _raise_timeout)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer != (0.0, 0.0):
            signal.setitimer(signal.ITIMER_REAL, *previous_timer)


def make_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_hvac_doclevel_extraction_batch"


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


def assemble_doc_text(rows: list[tuple[ContentChunk, DocumentPage, Document]]) -> str:
    parts = []
    for chunk, _, _ in rows:
        text = chunk.cleaned_text or chunk.text_excerpt or ""
        parts.extend([f"[[page={chunk.page_no} chunk_id={chunk.chunk_id}]]", sanitize_text(text)])
    return "\n\n".join(parts)


def sanitize_text(text: str) -> str:
    return "".join(char if char in "\n\r\t" or ord(char) >= 32 else " " for char in text)


def estimate_tokens(text: str) -> int:
    cjk = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    return int(cjk / 2 + (len(text) - cjk) / 4)


def known_equipment_scope(item: SourceItem, valid_ids: set[str]) -> str | None:
    scopes = [part.strip() for part in item.equipment_scope.split(",") if part.strip()]
    return scopes[0] if len(scopes) == 1 and scopes[0] in valid_ids else None


def resolve_equipment(rows: list[tuple[ContentChunk, DocumentPage, Document]], item: SourceItem) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    client = SwBaseModelOntologyClient()
    db = SessionLocal()
    try:
        profiles = build_equipment_profiles(db, "hvac", client)
    finally:
        db.close()
    text = normalize_text(" ".join([item.path.name, rows[0][2].file_name] + [chunk.cleaned_text for chunk, _, _ in rows]))
    equipment_id = known_equipment_scope(item, {profile.ontology_class_id for profile in profiles})
    match, alternatives = match_equipment_class(profiles, text, equipment_id)
    if match is None:
        match, alternatives = match_equipment_class(profiles, text, "controller")
    return match, alternatives, client.ontology_version()


def build_extract_messages(item: SourceItem, doc: Document, equipment: dict[str, Any], text: str, allowed_types: list[str], target: int) -> list[dict[str, str]]:
    system = (
        "You are a senior HVAC knowledge engineer. Extract high-value, reviewable knowledge objects from one OEM "
        "manual. Treat chunks only as evidence anchors. Return fewer high-confidence items rather than noisy coverage. "
        "Every evidence_quote MUST be a verbatim contiguous substring from the manual. Do not invent facts. "
        "Keep evidence_quote short: one exact label, one fault display line, one table row, or one complete sentence. "
        "Do not copy full tables, multi-row tables, or multi-paragraph troubleshooting blocks. Keep evidence_quote "
        "under 240 characters. If a table contains useful data, extract one row or one short cell group at a time. "
        f"Allowed knowledge_type values: {', '.join(allowed_types)}. "
        "Use fault_code for explicit codes and meanings; parameter_spec for configurable setpoints, limits, modes, "
        "defaults, and ranges; performance_spec for design/rated capacities and operating limits; maintenance_procedure "
        "for service actions; diagnostic_step or fault_diagnostic_rule for troubleshooting logic; application_guidance "
        "for installation/application constraints; operational_sequence for control behavior. "
        "Do not extract marketing claims, UI navigation instructions, pure product naming rules, isolated terminal labels, "
        "or text that cannot stand as a useful knowledge object. Return strict compact JSON only. Keep title, summary, "
        "and evidence_quote short. Do not include Markdown, comments, raw newline characters, or literal line breaks "
        "inside JSON string values; escape any unavoidable newline as \\n."
    )
    user = (
        f"Publisher/brand guess: {item.brand}\n"
        f"Document kind: {item.document_kind}\n"
        f"Equipment class: {equipment['equipment_class_id']}\n"
        f"Manual filename: {doc.file_name}\n"
        f"Target max candidates: {target}\n\n"
        f"Manual content with anchors:\n{text}\n\n"
        "Return JSON shape:\n"
        '{"candidates":[{"knowledge_type":"parameter_spec","title":"...","canonical_key_hint":null,'
        '"summary":"...","structured_payload":{"parameter_name":"..."},"evidence_quote":"exact source quote",'
        '"page_hint":1,"confidence":0.9}],"skipped_reason":null}\n'
        "Return one-line minified JSON when possible. Stop after the target max candidates exactly. "
        "Prefer 8-20 strong candidates over broad coverage. Do not continue past the target. "
        "Do not output partial JSON."
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def normalize_anchor(text: str) -> str:
    lowered = text.lower().replace("％", "%").replace("（", "(").replace("）", ")")
    return re.sub(r"[\s\u00a0，。；、,.;:：]+", "", lowered).strip()


def anchor_candidates(candidates: list[dict[str, Any]], rows: list[tuple[ContentChunk, DocumentPage, Document]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    chunks = [(chunk, page, normalize_anchor(chunk.cleaned_text or chunk.text_excerpt or "")) for chunk, page, _ in rows]
    anchored, rejected = [], []
    for candidate in candidates:
        quote = normalize_anchor(str(candidate.get("evidence_quote") or ""))
        matches = [(chunk, page) for chunk, page, text in chunks if quote and quote in text]
        candidate = repair_candidate_quote(candidate, chunks, matches)
        matches = candidate.pop("_anchor_matches", matches)
        if not matches:
            rejected.append({**candidate, "rejection_reason": "evidence_quote not found in any chunk"})
            continue
        anchored.append(build_anchored(candidate, matches))
    return anchored, rejected


def repair_candidate_quote(candidate: dict[str, Any], chunks: list[tuple[ContentChunk, DocumentPage, str]], matches):
    if matches:
        return candidate
    repaired_matches = repair_matches(candidate, chunks)
    if not repaired_matches:
        return candidate
    repaired = copy.deepcopy(candidate)
    repaired["anchor_repair_reason"] = "matched compact code/title payload back to source chunk"
    repaired["_anchor_matches"] = repaired_matches
    return repaired


def repair_matches(candidate: dict[str, Any], chunks: list[tuple[ContentChunk, DocumentPage, str]]):
    terms = repair_terms(candidate)
    if not terms:
        return []
    matches = []
    for chunk, page, text in chunks:
        if any(term in text for term in terms):
            matches.append((chunk, page))
    return matches


def repair_terms(candidate: dict[str, Any]) -> list[str]:
    payload = candidate.get("structured_payload") or {}
    values = [payload.get("fault_code"), payload.get("display"), payload.get("parameter_name"), candidate.get("title")]
    terms = []
    for value in values:
        for part in re.split(r"[/,，、\s]+", str(value or "")):
            normalized = normalize_anchor(part)
            if len(normalized) >= 3 or re.match(r"^[a-z]+\d+", normalized):
                terms.append(normalized)
    return list(dict.fromkeys(terms))


def build_anchored(candidate: dict[str, Any], matches: list[tuple[ContentChunk, DocumentPage]]) -> dict[str, Any]:
    result = copy.deepcopy(candidate)
    chunk_ids = [chunk.chunk_id for chunk, _ in matches]
    pages = sorted({page.page_no for _, page in matches})
    result["chunk_id"] = chunk_ids[0]
    result["page_no"] = pages[0]
    result["source_chunk_ids"] = chunk_ids
    result["source_page_nos"] = pages
    result["evidence_text"] = matches[0][0].cleaned_text or matches[0][0].text_excerpt or ""
    result["trust_level"] = "L4" if len(chunk_ids) >= 2 else "L3"
    result["verification_reason"] = f"verbatim anchor match in {len(chunk_ids)} chunk(s)"
    return result


def canonical_key(raw: str, domain: str, equipment_id: str, ko_type: str, fallback: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", (raw or fallback).strip().lower()).strip("_")
    return f"{domain}:{equipment_id}:{ko_type}:{value or 'candidate'}"


def candidate_entry(item: dict[str, Any], doc: Document, equipment: dict[str, Any], backend: OpenAICompatibleBackend, ontology_version: str) -> dict[str, Any]:
    ko_type = str(item["knowledge_type"])
    key = canonical_key(item.get("canonical_key_hint") or item["title"], str(doc.source_domain or "hvac"), equipment["equipment_class_id"], ko_type, item["summary"])
    payload = dict(item.get("structured_payload") or {})
    payload.setdefault("title", item["title"])
    payload.setdefault("summary", item["summary"])
    return {
        "candidate_id": stable_candidate_id(doc.doc_id, equipment["equipment_class_key"], key, item["evidence_quote"]),
        "domain_id": doc.source_domain or "hvac",
        "doc_id": doc.doc_id,
        "doc_name": doc.file_name,
        "page_no": item["page_no"],
        "chunk_id": item["chunk_id"],
        "knowledge_object_type": ko_type,
        "canonical_key_candidate": key,
        "structured_payload_candidate": payload,
        "confidence_score": round(float(item.get("confidence") or 0.0), 3),
        "review_status": "candidate",
        "evidence_text": item["evidence_text"],
        "curated_against_ontology_version": ontology_version,
        "equipment_class_candidate": equipment_candidate(equipment),
        "compile_metadata": {"method": "llm_doclevel_batch", "backend_name": backend.name, "model": backend.model},
        "source_chunk_ids": item.get("source_chunk_ids", []),
        "source_page_nos": item.get("source_page_nos", []),
        "trust_level": item.get("trust_level", "L3"),
    }


def equipment_candidate(equipment: dict[str, Any]) -> dict[str, Any]:
    return {
        "equipment_class_id": equipment["equipment_class_id"],
        "equipment_class_key": equipment["equipment_class_key"],
        "label": equipment["label"],
        "confidence": equipment["confidence"],
        "matched_aliases": equipment.get("matched_aliases", []),
        "supported_knowledge_anchors": list(equipment.get("knowledge_anchors", [])),
    }


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, default=str) + "\n" for row in rows), encoding="utf-8")


def usage(raw: dict[str, Any]) -> dict[str, int]:
    item = raw.get("response", {}).get("usage", {})
    prompt = int(item.get("prompt_tokens") or 0)
    completion = int(item.get("completion_tokens") or 0)
    return {"prompt_tokens": prompt, "completion_tokens": completion, "total_tokens": prompt + completion}


def cost_rmb(raw: dict[str, Any], pricing: dict[str, Any]) -> float:
    tokens = usage(raw)
    return round(tokens["prompt_tokens"] / 1000 * float(pricing.get("prompt_price_rmb_per_1k") or 0) + tokens["completion_tokens"] / 1000 * float(pricing.get("completion_price_rmb_per_1k") or 0), 6)


def request_json_completion_with_retry(
    messages: list[dict[str, str]],
    backend: OpenAICompatibleBackend,
    *,
    response_format: dict[str, Any] | None = None,
    recorder=None,
    attempts: int = 3,
) -> dict[str, Any]:
    last_error: Exception | None = None
    last_attempt_raw: dict[str, Any] = {}

    def _record(value: dict[str, Any]) -> None:
        last_attempt_raw.clear()
        last_attempt_raw.update(value)
        if recorder is not None:
            recorder(value)

    for attempt in range(1, attempts + 1):
        try:
            with wall_clock_timeout(backend.timeout_seconds, label=f"{backend.name} JSON request"):
                return _request_json_completion(messages, backend, response_format=response_format, recorder=_record)
        except (RuntimeError, json.JSONDecodeError, http.client.RemoteDisconnected, TimeoutError) as exc:
            if last_attempt_raw.get("response"):
                content = response_content_text(last_attempt_raw["response"])
                if content and len(content) <= 20000:
                    try:
                        with wall_clock_timeout(90, label=f"{backend.name} JSON repair request"):
                            return repair_json_response_with_backend(content, backend, recorder=_record)
                    except Exception:
                        pass
            last_error = exc
            if attempt == attempts:
                break
            time.sleep(min(20, 3 * attempt))
    raise RuntimeError(f"LLM JSON request failed after {attempts} attempts: {last_error}") from last_error


def build_judge_messages(entries: list[dict[str, Any]], doc: Document, equipment: dict[str, Any]) -> list[dict[str, str]]:
    items = [
        {
            "candidate_id": entry["candidate_id"],
            "knowledge_type": entry["knowledge_object_type"],
            "title": entry["structured_payload_candidate"].get("title"),
            "summary": entry["structured_payload_candidate"].get("summary"),
            "structured_payload": entry["structured_payload_candidate"],
            "evidence": entry.get("evidence_quote") or entry.get("evidence_text"),
            "source_pages": entry.get("source_page_nos"),
            "trust_level": entry.get("trust_level"),
        }
        for entry in entries
    ]
    system = (
        "You are a senior HVAC knowledge-base reviewer. Validate extracted knowledge objects from one equipment "
        "manual. Accept only useful, grounded, reviewable operational knowledge supported by the evidence. Reject "
        "marketing claims, UI-only navigation, isolated terminal labels, pure part names, duplicate/noisy items, "
        "generic prose with no operational value, or items whose evidence does not support the structured payload. "
        f"Supported knowledge_type values: {', '.join(SUPPORTED_TYPES)}. Reply with strict JSON only."
    )
    user = (
        f"Manual filename: {doc.file_name}\n"
        f"Equipment class: {equipment['equipment_class_id']}\n\n"
        "Review every candidate below. Preserve candidate_id exactly.\n"
        "Allowed category_if_not values: null, marketing, ui_behavior, terminal_label, part_name, duplicate, "
        "unsupported_type, weak_evidence, other.\n\n"
        f"{json.dumps({'candidates': items}, ensure_ascii=False)}\n\n"
        'Return JSON shape: {"verdicts":[{"candidate_id":"...","is_valid_hvac_knowledge":true,'
        '"reason":"short reason","category_if_not":null}]}'
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def judge_entries(entries: list[dict[str, Any]], backend: OpenAICompatibleBackend, doc: Document, equipment: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if not entries:
        return [], [], {}
    raw: dict[str, Any] = {}
    started = time.monotonic()
    payload = request_json_completion_with_retry(
        build_judge_messages(entries, doc, equipment),
        backend,
        response_format={"type": "json_object"},
        recorder=lambda value: raw.update(value),
    )
    raw["elapsed_seconds"] = round(time.monotonic() - started, 3)
    verdicts = {item.candidate_id: item for item in HvacJudgeResponse.model_validate(payload).verdicts}
    accepted, rejected = [], []
    for entry in entries:
        verdict = verdicts.get(entry["candidate_id"])
        if verdict and verdict.is_valid_hvac_knowledge:
            accepted.append({**entry, "judge_verdict": "accepted", "judge_reason": verdict.reason})
        else:
            reason = verdict.reason if verdict else "Judge response omitted candidate_id."
            category = verdict.category_if_not if verdict else "other"
            rejected.append({**entry, "judge_verdict": "rejected_by_judge", "judge_reason": reason, "judge_category": category})
    return accepted, rejected, raw


def extract_one(backend: OpenAICompatibleBackend, item: SourceItem, rows: list[tuple[ContentChunk, DocumentPage, Document]], equipment: dict[str, Any], args: argparse.Namespace) -> tuple[list[HvacDocCandidate], dict[str, Any]]:
    raw: dict[str, Any] = {}
    text = assemble_doc_text(rows)
    messages = build_extract_messages(item, rows[0][2], equipment, text, args.knowledge_types, args.target_candidates)
    started = time.monotonic()
    payload = request_json_completion_with_retry(messages, backend, recorder=lambda value: raw.update(value))
    raw["elapsed_seconds"] = round(time.monotonic() - started, 3)
    return HvacDocExtractionResponse.model_validate(payload).candidates, raw


def ensure_rows(item: SourceItem, args: argparse.Namespace) -> tuple[str, list[tuple[ContentChunk, DocumentPage, Document]], dict[str, Any]]:
    storage = StorageManager(settings.storage_root)
    doc_id, import_status = ensure_document_imported(item, storage=storage)
    processing = ensure_parsed_and_chunked(doc_id, storage=storage) if args.execute else {}
    rows = load_rows(doc_id)
    if not rows:
        raise ValueError(f"No chunks for {doc_id}; rerun with --execute")
    return doc_id, rows, {"import_status": import_status, "processing": processing}


def backend_result(args, backend_name: str, item: SourceItem, rows, equipment, ontology_version: str, output_dir: Path) -> dict[str, Any]:
    backend, pricing = load_backend(backend_name)
    if args.backend_timeout_seconds:
        backend = replace(backend, timeout_seconds=args.backend_timeout_seconds)
    if not backend.api_key:
        return {"backend": backend_name, "status": "skipped_missing_api_key"}
    backend_dir = output_dir / backend.name
    backend_dir.mkdir(parents=True, exist_ok=True)
    if not args.force and (backend_dir / "candidates.json").exists():
        print(f"skip existing backend={backend.name} task={item.row_index}", flush=True)
        return summarize_existing_backend(backend, pricing, backend_dir)
    try:
        print(
            f"start backend={backend.name} task={item.row_index} pages={len({row[1].page_no for row in rows})} "
            f"chunks={len(rows)} timeout={backend.timeout_seconds}s",
            flush=True,
        )
        candidates, raw = extract_one(backend, item, rows, equipment, args)
        raw_dicts = [candidate.model_dump() for candidate in candidates]
        anchored, rejected = anchor_candidates(raw_dicts, rows)
        entries = [candidate_entry(row, rows[0][2], equipment, backend, ontology_version) for row in anchored]
        accepted, judge_rejected, raw_judge, judge_cost = run_judge_if_requested(args, entries, rows[0][2], equipment)
        final_entries = accepted if args.judge_backend else entries
        write_backend_outputs(backend_dir, final_entries, raw_dicts, rejected, judge_rejected, raw, raw_judge, args)
        print(
            f"done backend={backend.name} task={item.row_index} raw={len(raw_dicts)} "
            f"anchored={len(anchored)} final={len(final_entries)}",
            flush=True,
        )
        return summarize_backend(
            backend,
            pricing,
            raw,
            raw_judge,
            judge_cost,
            bool(args.judge_backend),
            raw_dicts,
            anchored,
            rejected,
            judge_rejected,
            final_entries,
            backend_dir,
        )
    except Exception as exc:
        if raw:
            write_json(backend_dir / "raw_extract_response.json", raw)
        write_json(backend_dir / "error.json", {"error": str(exc), "error_type": type(exc).__name__})
        print(f"failed backend={backend.name} task={item.row_index}: {type(exc).__name__}: {exc}", flush=True)
        return {"backend": backend.name, "model": backend.model, "status": "failed", "error": str(exc)}


def run_judge_if_requested(args, entries, doc, equipment) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], float]:
    if not args.judge_backend:
        return entries, [], {}, 0.0
    if not entries:
        return [], [], {}, 0.0
    judge_backend, judge_pricing = load_backend(args.judge_backend)
    if args.backend_timeout_seconds:
        judge_backend = replace(judge_backend, timeout_seconds=args.backend_timeout_seconds)
    if not judge_backend.api_key:
        raise ValueError(f"judge backend {judge_backend.name} has no api_key")
    accepted, rejected, raw = judge_entries(entries, judge_backend, doc, equipment)
    return accepted, rejected, raw, cost_rmb(raw, judge_pricing)


def write_backend_outputs(output_dir: Path, entries, raw_candidates, anchor_rejected, judge_rejected, raw_response, raw_judge, args) -> None:
    stale_error = output_dir / "error.json"
    if stale_error.exists():
        stale_error.unlink()
    candidate_path = output_dir / "candidates.json"
    write_json(candidate_path, {"generation_mode": "llm_doclevel_batch", "domain_id": "hvac", "filters_applied": {}, "candidate_entries": entries})
    write_jsonl(output_dir / "candidates_raw.jsonl", raw_candidates)
    write_jsonl(output_dir / "candidates_anchor_rejected.jsonl", anchor_rejected)
    write_jsonl(output_dir / "candidates_judge_rejected.jsonl", judge_rejected)
    write_json(output_dir / "raw_extract_response.json", raw_response)
    if raw_judge:
        write_json(output_dir / "raw_judge_response.json", raw_judge)
    pack_dir = output_dir / "review_packs"
    manifest = write_review_packs_from_candidate_file(candidate_path, pack_dir, default_trust_level=args.default_trust_level)
    bootstrap = bootstrap_review_pack_directory(pack_dir, default_trust_level=args.default_trust_level)
    readiness = check_review_pack_directory(Path(bootstrap["output_dir"]))
    write_json(
        output_dir / "review_bundle_summary.json",
        {"review_pack_manifest": manifest, "bootstrap": bootstrap, "readiness": readiness, "judge_enabled": bool(args.judge_backend)},
    )


def summarize_backend(backend, pricing, raw, raw_judge, judge_cost, judge_enabled, raw_candidates, anchored, rejected, judge_rejected, entries, output_dir: Path) -> dict[str, Any]:
    by_type = Counter(entry["knowledge_object_type"] for entry in entries)
    anchor_rate = len(anchored) / len(raw_candidates) * 100 if raw_candidates else 100.0
    judge_total = len(entries) + len(judge_rejected)
    judge_rate = len(entries) / judge_total * 100 if judge_total else 100.0
    extract_cost = cost_rmb(raw, pricing)
    return {
        "backend": backend.name,
        "model": backend.model,
        "status": "ok",
        "judge_enabled": judge_enabled,
        "raw_candidates": len(raw_candidates),
        "anchor_passed": len(anchored),
        "anchor_rejected": len(rejected),
        "anchor_match_rate": round(anchor_rate, 1),
        "judge_accepted": len(entries),
        "judge_rejected": len(judge_rejected),
        "judge_acceptance_rate": round(judge_rate, 1),
        "judge_rejection_breakdown": dict(Counter(row.get("judge_category") or "other" for row in judge_rejected)),
        "review_candidates": len(entries),
        "by_type": dict(by_type),
        "usage": usage(raw),
        "judge_usage": usage(raw_judge),
        "extract_cost_rmb": extract_cost,
        "judge_cost_rmb": judge_cost,
        "cost_rmb": round(extract_cost + judge_cost, 6),
        "elapsed_seconds": raw.get("elapsed_seconds"),
        "judge_elapsed_seconds": raw_judge.get("elapsed_seconds"),
        "output_dir": str(output_dir),
    }


def summarize_existing_backend(backend, pricing, output_dir: Path) -> dict[str, Any]:
    candidates_path = output_dir / "candidates.json"
    raw_path = output_dir / "raw_extract_response.json"
    raw_judge_path = output_dir / "raw_judge_response.json"
    rejected_path = output_dir / "candidates_anchor_rejected.jsonl"
    judge_rejected_path = output_dir / "candidates_judge_rejected.jsonl"
    candidate_payload = json.loads(candidates_path.read_text(encoding="utf-8"))
    entries = candidate_payload.get("candidate_entries", [])
    raw = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else {}
    raw_judge = json.loads(raw_judge_path.read_text(encoding="utf-8")) if raw_judge_path.exists() else {}
    rejected_count = len(rejected_path.read_text(encoding="utf-8").splitlines()) if rejected_path.exists() else 0
    judge_rejected_count = len(judge_rejected_path.read_text(encoding="utf-8").splitlines()) if judge_rejected_path.exists() else 0
    by_type = Counter(entry["knowledge_object_type"] for entry in entries)
    raw_count = len(entries) + rejected_count + judge_rejected_count
    anchor_passed = len(entries) + judge_rejected_count
    anchor_rate = anchor_passed / raw_count * 100 if raw_count else 100.0
    judge_rate = len(entries) / anchor_passed * 100 if anchor_passed else 100.0
    return {
        "backend": backend.name,
        "model": backend.model,
        "status": "ok_existing",
        "judge_enabled": raw_judge_path.exists(),
        "raw_candidates": raw_count,
        "anchor_passed": anchor_passed,
        "anchor_rejected": rejected_count,
        "anchor_match_rate": round(anchor_rate, 1),
        "judge_accepted": len(entries),
        "judge_rejected": judge_rejected_count,
        "judge_acceptance_rate": round(judge_rate, 1),
        "review_candidates": len(entries),
        "by_type": dict(by_type),
        "usage": usage(raw),
        "judge_usage": usage(raw_judge),
        "cost_rmb": cost_rmb(raw, pricing),
        "elapsed_seconds": raw.get("elapsed_seconds"),
        "judge_elapsed_seconds": raw_judge.get("elapsed_seconds"),
        "output_dir": str(output_dir),
    }


def render_report(summary: dict[str, Any]) -> str:
    lines = ["# HVAC Doc-Level Extraction Batch Report", "", f"- Run ID: `{summary['run_id']}`", f"- Output dir: `{summary['output_dir']}`", ""]
    for task in summary["tasks"]:
        lines.extend(render_task(task))
    return "\n".join(lines) + "\n"


def render_task(task: dict[str, Any]) -> list[str]:
    rows = ["## " + task["file_name"], "", f"- doc_id: `{task.get('doc_id')}`", f"- equipment: `{task.get('equipment_class_id')}`", ""]
    rows.extend(["| Backend | Status | Raw | Anchored | Final | Anchor rate | Judge rate | Types | Seconds | Cost |", "|---|---|---:|---:|---:|---:|---:|---|---:|---:|"])
    for result in task["backend_results"]:
        rows.append("| " + " | ".join(backend_cells(result)) + " |")
    return rows + [""]


def backend_cells(result: dict[str, Any]) -> list[str]:
    return [
        str(result.get("backend")),
        str(result.get("status")),
        str(result.get("raw_candidates", "-")),
        str(result.get("anchor_passed", "-")),
        str(result.get("review_candidates", "-")),
        str(result.get("anchor_match_rate", "-")),
        str(result.get("judge_acceptance_rate", "-")),
        ", ".join(f"{k}:{v}" for k, v in (result.get("by_type") or {}).items()) or "-",
        str(result.get("elapsed_seconds", "-")),
        f"¥{float(result.get('cost_rmb') or 0):.4f}",
    ]


def run(args: argparse.Namespace) -> dict[str, Any]:
    items = select_items(load_manifest(args.manifest), groups=set(args.groups), limit=args.limit)
    batch_dir = Path(args.resume_dir) if args.resume_dir else Path(args.output_dir) / make_run_id()
    batch_dir.mkdir(parents=True, exist_ok=bool(args.resume_dir))
    tasks = load_existing_task_summaries(batch_dir) if args.resume_dir else []
    completed_indexes = {
        int(task["row_index"])
        for task in tasks
        if not args.force and task_complete_for_backends(task, args.backends, args.judge_backend)
    }
    summary = {"run_id": batch_dir.name, "output_dir": str(batch_dir), "tasks": tasks}
    write_batch_summary(batch_dir, summary)
    for item in items:
        if item.row_index in completed_indexes:
            print(f"skip completed task={item.row_index}", flush=True)
            continue
        tasks = replace_task(tasks, run_item(args, item, batch_dir))
        summary = {"run_id": batch_dir.name, "output_dir": str(batch_dir), "tasks": tasks}
        write_batch_summary(batch_dir, summary)
    return summary


def load_existing_task_summaries(batch_dir: Path) -> list[dict[str, Any]]:
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(batch_dir.glob("*/task_summary.json"))
    ]


def task_complete_for_backends(task: dict[str, Any], backends: list[str], judge_backend: str = "") -> bool:
    if task.get("status") != "completed":
        return False
    results = {str(item.get("backend")): item for item in task.get("backend_results", [])}
    complete_statuses = {"ok", "ok_existing", "skipped_missing_api_key"}
    for backend in backends:
        result = results.get(backend)
        if not result or str(result.get("status")) not in complete_statuses:
            return False
        if judge_backend and result.get("status") != "skipped_missing_api_key" and not result.get("judge_enabled"):
            return False
    return True


def replace_task(tasks: list[dict[str, Any]], task: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        [existing for existing in tasks if existing.get("row_index") != task.get("row_index")] + [task],
        key=lambda item: int(item.get("row_index") or 0),
    )


def write_batch_summary(batch_dir: Path, summary: dict[str, Any]) -> None:
    write_json(batch_dir / "summary.json", summary)
    (batch_dir / "REPORT.md").write_text(render_report(summary), encoding="utf-8")


def run_item(args: argparse.Namespace, item: SourceItem, batch_dir: Path) -> dict[str, Any]:
    task_dir = batch_dir / f"{item.row_index:04d}_{slugify(item.path.stem)}"
    task_dir.mkdir(parents=True, exist_ok=True)
    try:
        print(f"start task={item.row_index} file={item.path.name}", flush=True)
        doc_id, rows, processing = ensure_rows(item, args)
        equipment, alternatives, ontology_version = resolve_equipment(rows, item)
        results = [backend_result(args, name, item, rows, equipment, ontology_version, task_dir) for name in args.backends]
        task = build_task_summary(item, doc_id, rows, equipment, alternatives, processing, results, task_dir)
        print(f"done task={item.row_index}", flush=True)
        return task
    except Exception as exc:
        task = {"row_index": item.row_index, "file_name": item.path.name, "status": "failed", "error": str(exc), "task_dir": str(task_dir)}
        write_json(task_dir / "task_summary.json", task)
        print(f"failed task={item.row_index}: {type(exc).__name__}: {exc}", flush=True)
        return task


def build_task_summary(item, doc_id, rows, equipment, alternatives, processing, results, task_dir) -> dict[str, Any]:
    payload = {
        "status": task_status_from_backend_results(results),
        "row_index": item.row_index,
        "file_name": item.path.name,
        "source_path": str(item.path),
        "doc_id": doc_id,
        "chunks": len(rows),
        "manual_tokens_estimated": estimate_tokens(assemble_doc_text(rows)),
        "equipment_class_id": equipment["equipment_class_id"],
        "equipment_alternatives": alternatives,
        "processing": processing,
        "backend_results": results,
        "task_dir": str(task_dir),
    }
    write_json(task_dir / "task_summary.json", payload)
    return payload


def task_status_from_backend_results(results: list[dict[str, Any]]) -> str:
    statuses = {str(result.get("status") or "") for result in results}
    if statuses & {"ok", "ok_existing"}:
        return "completed"
    if statuses and statuses <= {"skipped_missing_api_key"}:
        return "skipped"
    return "failed"


def slugify(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "_", value).strip("_").lower()[:96] or "doc"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--groups", default="B_oem_manual_text_first")
    parser.add_argument("--output-dir", default="output/hvac_doclevel_extraction_batch")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--execute", action="store_true", help="Import/parse/chunk before extraction if needed")
    parser.add_argument("--backends", default="deepseek-parameter-spec,mimo-v2.5-pro")
    parser.add_argument("--judge-backend", default="", help="Optional second backend to model-review anchored candidates")
    parser.add_argument("--knowledge-types", default=",".join(SUPPORTED_TYPES))
    parser.add_argument("--target-candidates", type=int, default=10)
    parser.add_argument("--default-trust-level", default="L3")
    parser.add_argument("--resume-dir", help="Existing batch run directory to resume")
    parser.add_argument("--force", action="store_true", help="Re-run tasks/backends even if output already exists")
    parser.add_argument("--backend-timeout-seconds", type=int, help="Override all backend request timeouts for this run")
    return parser


def normalize_args(args: argparse.Namespace) -> argparse.Namespace:
    args.backends = [name.strip() for name in args.backends.split(",") if name.strip()]
    args.groups = {name.strip() for name in args.groups.split(",") if name.strip()}
    args.knowledge_types = [name.strip() for name in args.knowledge_types.split(",") if name.strip()]
    args.judge_backend = args.judge_backend.strip()
    return args


def main(argv: list[str] | None = None) -> int:
    summary = run(normalize_args(build_parser().parse_args(argv)))
    report = Path(summary["output_dir"]) / "REPORT.md"
    print(f"doclevel batch tasks={len(summary['tasks'])} report={report}")
    return 1 if any(task.get("status") == "failed" for task in summary["tasks"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
