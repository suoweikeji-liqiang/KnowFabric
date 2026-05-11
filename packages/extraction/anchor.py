"""Verbatim chunk anchoring — match LLM evidence_quotes back to source chunks."""

from __future__ import annotations

import copy
import re
from typing import Any


def normalize_anchor(text: str) -> str:
    lowered = text.lower().replace("％", "%").replace("（", "(").replace("）", ")")
    return re.sub(r"[\s ，。；、,.;:：]+", "", lowered).strip()


def anchor_candidates(
    candidates: list[dict[str, Any]],
    chunk_records: list[tuple[Any, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Match candidate evidence_quotes to source chunks via verbatim substring.

    Args:
        candidates: List of candidate dicts with 'evidence_quote' key.
        chunk_records: List of (ContentChunk, DocumentPage) tuples.

    Returns:
        (anchored_candidates, rejected_candidates).
    """
    chunks = [
        (chunk, page, normalize_anchor(chunk.cleaned_text or chunk.text_excerpt or ""))
        for chunk, page in chunk_records
    ]
    anchored, rejected = [], []
    for candidate in candidates:
        quote = normalize_anchor(str(candidate.get("evidence_quote") or ""))
        matches = [(chunk, page) for chunk, page, text in chunks if quote and quote in text]
        candidate = _repair_candidate_quote(candidate, chunks, matches)
        matches = candidate.pop("_anchor_matches", matches)
        if not matches:
            rejected.append({**candidate, "rejection_reason": "evidence_quote not found in any chunk"})
            continue
        anchored.append(build_anchored(candidate, matches))
    return anchored, rejected


def _repair_candidate_quote(
    candidate: dict[str, Any],
    chunks: list[tuple[Any, Any, str]],
    matches: list,
) -> dict[str, Any]:
    if matches:
        return candidate
    repaired_matches = _repair_matches(candidate, chunks)
    if not repaired_matches:
        return candidate
    repaired = copy.deepcopy(candidate)
    repaired["anchor_repair_reason"] = "matched compact code/title payload back to source chunk"
    repaired["_anchor_matches"] = repaired_matches
    return repaired


def _repair_matches(
    candidate: dict[str, Any],
    chunks: list[tuple[Any, Any, str]],
) -> list[tuple[Any, Any]]:
    terms = _repair_terms(candidate)
    if not terms:
        return []
    matches = []
    for chunk, page, text in chunks:
        if any(term in text for term in terms):
            matches.append((chunk, page))
    return matches


def _repair_terms(candidate: dict[str, Any]) -> list[str]:
    payload = candidate.get("structured_payload") or {}
    values = [
        payload.get("fault_code"),
        payload.get("display"),
        payload.get("parameter_name"),
        candidate.get("title"),
    ]
    terms = []
    for value in values:
        for part in re.split(r"[/,，、\s]+", str(value or "")):
            normalized = normalize_anchor(part)
            if len(normalized) >= 3 or re.match(r"^[a-z]+\d+", normalized):
                terms.append(normalized)
    return list(dict.fromkeys(terms))


def build_anchored(
    candidate: dict[str, Any],
    matches: list[tuple[Any, Any]],
) -> dict[str, Any]:
    result = copy.deepcopy(candidate)
    chunk_ids = [chunk.chunk_id for chunk, _ in matches]
    pages = sorted({page.page_no for _, page in matches})
    result["chunk_id"] = chunk_ids[0]
    result["page_no"] = pages[0]
    result["source_chunk_ids"] = chunk_ids
    result["source_page_nos"] = pages
    result["evidence_text"] = matches[0][0].cleaned_text or matches[0][0].text_excerpt or ""
    result["verification_reason"] = f"verbatim anchor match in {len(chunk_ids)} chunk(s)"
    return result
