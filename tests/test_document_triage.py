"""Tests for ingest-time document triage decisions."""

from __future__ import annotations

from dataclasses import dataclass

from packages.ingest.document_triage import ProcessingDecision, triage_document


@dataclass
class DocStub:
    file_ext: str = "pdf"
    authority_level: str = "oem_manual"
    text_quality: str = "good_text"
    page_count: int | None = 10
    file_size_mb: float | None = 1.0
    document_kind: str = "manual"
    authority_metadata_json: dict | None = None


def decision(doc: DocStub) -> ProcessingDecision:
    return triage_document(doc).decision


def test_vendor_app_note_low_or_no_text_is_discarded() -> None:
    doc = DocStub(authority_level="vendor_app_note", text_quality="low_or_no_text")
    assert decision(doc) == ProcessingDecision.DISCARD


def test_industry_standard_good_text_is_keep_text() -> None:
    doc = DocStub(authority_level="industry_standard", text_quality="good_text", page_count=83)
    assert decision(doc) == ProcessingDecision.KEEP_TEXT


def test_oem_manual_low_or_no_text_routes_visual() -> None:
    doc = DocStub(authority_level="oem_manual", text_quality="low_or_no_text", page_count=81)
    assert decision(doc) == ProcessingDecision.KEEP_VISUAL


def test_standard_scanned_needs_ocr() -> None:
    doc = DocStub(authority_level="regulatory_code", text_quality="low_or_no_text")
    assert decision(doc) == ProcessingDecision.NEEDS_OCR_CONVERT


def test_standard_doc_file_goes_to_manual_review() -> None:
    doc = DocStub(file_ext="doc", authority_level="industry_standard", text_quality="unknown")
    assert decision(doc) == ProcessingDecision.MANUAL_REVIEW


def test_unknown_quality_with_oem_manual_goes_to_manual_review() -> None:
    doc = DocStub(authority_level="oem_manual", text_quality="unknown", page_count=None)
    assert decision(doc) == ProcessingDecision.MANUAL_REVIEW


def test_unsupported_file_extension_is_discarded() -> None:
    doc = DocStub(file_ext="pptx", authority_level="industry_standard", text_quality="good_text")
    assert decision(doc) == ProcessingDecision.DISCARD


def test_metadata_fallback_fields_are_used() -> None:
    doc = DocStub(
        file_ext="",
        authority_level="",
        text_quality="",
        page_count=None,
        authority_metadata_json={
            "file_ext": "pdf",
            "authority_level": "industry_standard_or_reference",
            "text_quality": "partial_text",
            "page_count": "14",
        },
    )
    result = triage_document(doc)
    assert result.decision == ProcessingDecision.KEEP_TEXT
    assert "industry/regulatory text quality" in result.reason
