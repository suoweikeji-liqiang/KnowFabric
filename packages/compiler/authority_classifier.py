"""Auto-classify document authority_level from metadata and filename heuristics.

Rule-first, LLM fallback. Updates Document.authority_level and related fields.
"""

from __future__ import annotations

import json
from typing import Any

from packages.compiler.llm_compiler import _request_json_completion, resolve_backend
from packages.db.models import Document

AUTHORITY_LEVELS = (
    "industry_standard",
    "regulatory_code",
    "oem_manual",
    "vendor_application_note",
    "internal_sop",
    "field_observation",
    "academic_reference",
    "unspecified",
)

OEM_BRANDS = {
    "trane", "york", "carrier", "daikin", "mcquay", "abb", "siemens",
    "honeywell", "johnson controls", "lg", "samsung", "mitsubishi",
    "hitachi", "toshiba", "panasonic", "schneider", "danfoss", "emerson",
    "特灵", "约克", "开利", "大金",
    "麦克维尔", "三菱", "日立", "格力",
    "美的", "海尔", "天加", "顿汉布什",
    "国祥",
}

STANDARD_KEYWORDS = [
    "ashrae", "guideline", "standard", "iec ", "iso ", "gb/t", "gb ",
    "en ", "bs ", "din ", "nfpa", "ul ", "csa ", "ahri",
    "标准", "规范", "国标",
]

REGULATORY_KEYWORDS = [
    "regulatory", "regulation", "code of federal", "building code",
    "法规", "强制", "规章",
]


def _matches_any(text: str, keywords: list[str]) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in keywords)


def classify_by_rules(doc: Document) -> dict[str, Any] | None:
    """Try to classify a document using filename/publisher heuristics.

    Returns a dict with: authority_level, publisher, standard_id, vendor_brand,
    vendor_model_family (all nullable), or None if rules can't decide.
    """
    result: dict[str, Any] = {
        "authority_level": None,
        "publisher": None,
        "standard_id": None,
        "vendor_brand": None,
        "vendor_model_family": None,
    }

    file_name = (doc.file_name or "").lower()
    publisher = (getattr(doc, "publisher", None) or "").lower()

    # Check standard keywords in filename
    for kw in STANDARD_KEYWORDS:
        if kw in file_name:
            result["authority_level"] = "industry_standard"
            result["standard_id"] = doc.file_name
            if "ashrae" in file_name:
                result["publisher"] = "ASHRAE"
            elif "iec" in file_name:
                result["publisher"] = "IEC"
            elif "iso" in file_name:
                result["publisher"] = "ISO"
            return result

    # Check regulatory keywords
    for kw in REGULATORY_KEYWORDS:
        if kw in file_name or kw in publisher:
            result["authority_level"] = "regulatory_code"
            result["standard_id"] = doc.file_name
            return result

    # Check OEM brands
    for brand in OEM_BRANDS:
        if brand in file_name or brand in publisher:
            result["authority_level"] = "oem_manual"
            result["publisher"] = brand.title()
            result["vendor_brand"] = brand.title()
            return result

    # Check for internal SOP
    if any(kw in file_name for kw in ["sop", "procedure", "checklist", "操作规程"]):
        result["authority_level"] = "internal_sop"
        return result

    # Check for academic
    if any(kw in file_name for kw in ["handbook", "textbook", "paper", "journal", "thesis"]):
        result["authority_level"] = "academic_reference"
        return result

    return None


def classify_with_llm(doc: Document, backend_name: str | None = None) -> dict[str, Any]:
    """Use LLM to classify a document's authority level."""
    backend = resolve_backend(backend_name=backend_name)
    if backend is None:
        raise RuntimeError("No LLM backend available for authority classification")

    messages = [
        {
            "role": "system",
            "content": (
                "You classify industrial technical documents by authority level. "
                f"Valid levels: {', '.join(AUTHORITY_LEVELS)}. "
                "Return only JSON: "
                '{"authority_level": "...", "publisher": null, "standard_id": null, '
                '"vendor_brand": null, "vendor_model_family": null, "rationale": "..."}'
            ),
        },
        {
            "role": "user",
            "content": json.dumps({
                "task": "authority_classification",
                "file_name": doc.file_name,
                "source_domain": doc.source_domain,
                "publisher": getattr(doc, "publisher", None),
                "standard_id": getattr(doc, "standard_id", None),
            }, ensure_ascii=False),
        },
    ]

    try:
        body = _request_json_completion(
            messages,
            backend,
            response_format={"type": "json_object"},
        )
    except Exception:
        body = {}

    if body.get("authority_level") not in AUTHORITY_LEVELS:
        body["authority_level"] = "unspecified"

    return {
        "authority_level": body.get("authority_level", "unspecified"),
        "publisher": body.get("publisher"),
        "standard_id": body.get("standard_id"),
        "vendor_brand": body.get("vendor_brand"),
        "vendor_model_family": body.get("vendor_model_family"),
    }


def classify_document(doc: Document, backend_name: str | None = None) -> dict[str, Any]:
    """Classify one document: rules first, LLM fallback.

    Returns a dict of fields to update on the Document row.
    """
    result = classify_by_rules(doc)
    if result is not None and result["authority_level"] is not None:
        return result
    try:
        return classify_with_llm(doc, backend_name=backend_name)
    except RuntimeError:
        return {
            "authority_level": "unspecified",
            "publisher": None,
            "standard_id": None,
            "vendor_brand": None,
            "vendor_model_family": None,
        }
