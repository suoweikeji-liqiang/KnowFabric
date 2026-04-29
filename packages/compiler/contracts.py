"""Shared contracts for compiler outputs and metadata."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from pydantic import BaseModel, Field

DEFAULT_COMPILER_VERSION = "2026-04-10"


class ParameterSpecCandidate(BaseModel):
    """Strict structured output shape for document-level parameter_spec extraction."""

    parameter_name: str = Field(description="Configurable parameter name as written in source")
    canonical_key_hint: str | None = Field(default=None, description="Suggested canonical key")
    value: str | None = None
    unit: str | None = None
    range_min: str | None = None
    range_max: str | None = None
    default_value: str | None = None
    description: str | None = None
    evidence_quote: str = Field(
        description="Verbatim text from manual that contains this parameter, MUST be exact substring of source"
    )
    page_hint: int | None = Field(default=None, description="Page number where parameter appears, if visible from chunk anchors")
    confidence: float = Field(ge=0.0, le=1.0)


class DocumentExtractionResponse(BaseModel):
    """Strict document-level extraction response."""

    candidates: list[ParameterSpecCandidate] = Field(default_factory=list)
    skipped_reason: str | None = Field(
        default=None,
        description="If no parameters extractable, populate this and leave candidates empty",
    )


ExtractionResponse = DocumentExtractionResponse


def build_compile_metadata(
    method: str,
    *,
    version: str = DEFAULT_COMPILER_VERSION,
    rationale: str | None = None,
    source_span_ids: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build normalized compiler provenance metadata."""

    payload = {
        "method": method,
        "version": version,
        "source_span_ids": list(source_span_ids or []),
    }
    if rationale:
        payload["rationale"] = rationale
    if extra:
        payload.update(extra)
    return payload


def attach_internal_metadata(
    structured_payload: dict[str, Any],
    *,
    compile_metadata: dict[str, Any] | None = None,
    health_signals: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach internal compiler/health metadata under underscored keys."""

    payload = deepcopy(structured_payload)
    if compile_metadata:
        payload["_compiler_metadata"] = deepcopy(compile_metadata)
    if health_signals:
        payload["_health_signals"] = deepcopy(health_signals)
    return payload


def extract_compile_metadata(structured_payload: dict[str, Any] | None) -> dict[str, Any]:
    """Extract compiler metadata from one stored structured payload."""

    if not isinstance(structured_payload, dict):
        return {}
    value = structured_payload.get("_compiler_metadata")
    return value if isinstance(value, dict) else {}


def extract_health_signals(structured_payload: dict[str, Any] | None) -> dict[str, Any]:
    """Extract health signals from one stored structured payload."""

    if not isinstance(structured_payload, dict):
        return {}
    value = structured_payload.get("_health_signals")
    return value if isinstance(value, dict) else {}


def public_health_flags(structured_payload: dict[str, Any] | None) -> list[str]:
    """Return the public health flags list stored in one structured payload."""

    payload = extract_health_signals(structured_payload)
    value = payload.get("flags")
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]
