"""Rule-based ingest triage for source documents."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class ProcessingDecision(StrEnum):
    DISCARD = "DISCARD"
    KEEP_TEXT = "KEEP_TEXT"
    KEEP_VISUAL = "KEEP_VISUAL"
    NEEDS_OCR_CONVERT = "NEEDS_OCR_CONVERT"
    MANUAL_REVIEW = "MANUAL_REVIEW"


@dataclass(frozen=True)
class TriageResult:
    decision: ProcessingDecision
    reason: str
    decided_at: datetime


SUPPORTED_EXTENSIONS = {"pdf", "docx", "doc", "xlsx"}
VENDOR_DISCARD_LEVELS = {"vendor_app_note", "vendor_training"}
INDUSTRY_LEVELS = {
    "industry_standard",
    "industry_standard_or_reference",
    "regulatory_code",
}
OEM_LEVELS = {"oem_manual"}
LOW_TEXT = {"low_or_no_text", "not_pdf", "unknown", ""}
TEXT_OK = {"good_text", "partial_text"}


def triage_document(document: Any) -> TriageResult:
    """Return a deterministic processing decision for a document-like object."""

    file_ext = _normalize_ext(_field(document, "file_ext", "suffix"))
    authority_level = _normalize(_field(document, "authority_level", "authority_level_guess"))
    text_quality = _normalize(_field(document, "text_quality"))
    page_count = _int_or_none(_field(document, "page_count"))
    file_size_mb = _float_or_none(_field(document, "file_size_mb", "size_mb"))
    now = datetime.now(timezone.utc)

    if file_ext not in SUPPORTED_EXTENSIONS:
        return TriageResult(ProcessingDecision.DISCARD, f"unsupported file_ext={file_ext or 'unknown'}", now)

    if authority_level in VENDOR_DISCARD_LEVELS:
        if text_quality in LOW_TEXT:
            return TriageResult(ProcessingDecision.DISCARD, f"{authority_level} with text_quality={text_quality or 'unknown'}", now)
        if page_count is not None and page_count < 5:
            return TriageResult(ProcessingDecision.DISCARD, f"{authority_level} page_count={page_count} below 5", now)
        if file_size_mb is not None and file_size_mb > 50 and text_quality == "low_or_no_text":
            return TriageResult(ProcessingDecision.DISCARD, f"{authority_level} large low-text file_size_mb={file_size_mb}", now)

    if authority_level in INDUSTRY_LEVELS:
        if file_ext in {"doc", "docx"}:
            return TriageResult(ProcessingDecision.MANUAL_REVIEW, "industry/regulatory Word document requires operator review", now)
        if text_quality in {"good_text", "partial_text"}:
            return TriageResult(ProcessingDecision.KEEP_TEXT, f"industry/regulatory text quality {text_quality}", now)
        if text_quality == "low_or_no_text":
            return TriageResult(ProcessingDecision.NEEDS_OCR_CONVERT, "industry/regulatory scanned document worth OCR", now)

    if authority_level in OEM_LEVELS:
        if text_quality in TEXT_OK:
            return TriageResult(ProcessingDecision.KEEP_TEXT, f"OEM manual text quality {text_quality}", now)
        if text_quality == "low_or_no_text":
            return TriageResult(ProcessingDecision.KEEP_VISUAL, "OEM low-text document routed to visual pipeline", now)

    return TriageResult(ProcessingDecision.MANUAL_REVIEW, "no deterministic triage rule matched", now)


def apply_triage_to_document(document: Any) -> TriageResult:
    """Apply triage result fields to an ORM/document-like row."""

    result = triage_document(document)
    setattr(document, "processing_decision", result.decision.value)
    setattr(document, "processing_decision_at", result.decided_at)
    setattr(document, "processing_decision_reason", result.reason)
    return result


def _field(document: Any, *names: str) -> Any:
    metadata = getattr(document, "authority_metadata_json", None) or {}
    for name in names:
        value = getattr(document, name, None)
        if value not in (None, ""):
            return value
        if isinstance(metadata, dict):
            value = metadata.get(name)
            if value not in (None, ""):
                return value
    return None


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower()


def _normalize_ext(value: Any) -> str:
    return _normalize(value).lstrip(".")


def _int_or_none(value: Any) -> int | None:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return None


def _float_or_none(value: Any) -> float | None:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None
