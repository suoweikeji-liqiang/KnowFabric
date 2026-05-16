"""MiMo page-image extraction for chiller parameter/fault candidates."""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib import error, request

from packages.compiler.rate_limited_client import MaxRetriesExceeded, RateLimitedClient
from packages.compiler.llm_compiler import OpenAICompatibleBackend, response_content_text, parse_json_response_content
from packages.extraction.visual import image_as_data_url

ALLOWED_TYPES = {"parameter_spec", "fault_code", "performance_spec"}


@dataclass(frozen=True)
class ExtractedCandidate:
    knowledge_object_type: str
    parameter_name: str
    structured_payload: dict[str, Any]
    evidence_quote: str
    page_no: int
    confidence: float
    raw: dict[str, Any]


def build_visual_parameter_messages(
    *,
    image_url: str,
    page_no: int,
    equipment_class_id: str,
) -> list[dict[str, Any]]:
    system = (
        "You are extracting industrial chiller parameter specifications from a SCANNED MANUAL PAGE IMAGE. "
        "Look at the image and identify:\n\n"
        "- parameter_spec: configurable setpoints, limits, default values, ranges, mode selections that an "
        "operator/commissioning engineer would set\n"
        "- fault_code: fault codes/alarms with their names and trigger conditions\n"
        "- performance_spec: rated capacities, operating limits, design conditions\n\n"
        "For each item:\n"
        "- parameter_name: concept name, using Chinese or English as it appears in the manual\n"
        "- value / range_min / range_max / default_value: numerical values with units when visible\n"
        "- unit: explicit unit (kPa / psi / ℃ / °F / A / etc.)\n"
        "- evidence_quote: SHORT verbatim text visible in the image (1 line or 1 row)\n"
        "- confidence: 0.0-1.0\n\n"
        "Return strict JSON only:\n"
        "{\"candidates\": [{\"knowledge_object_type\": \"parameter_spec\", \"parameter_name\": \"...\", "
        "\"value\": \"...\", \"unit\": \"...\", \"range_min\": \"...\", \"range_max\": \"...\", "
        "\"default_value\": \"...\", \"evidence_quote\": \"...\", \"page_no\": 1, \"confidence\": 0.0}]}\n\n"
        "Do not invent. If page is wiring diagram / cover / TOC / index / pure marketing, return candidates=[]."
    )
    user = (
        f"Equipment class: {equipment_class_id}\n"
        f"Page number: {page_no}\n"
        "Extract only visible, grounded parameter_spec, fault_code, and performance_spec candidates."
    )
    return [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        },
    ]


def extract_parameters_from_page_image(
    *,
    doc_id: str,
    page_no: int,
    rendered_image_path: Path,
    equipment_class_id: str,
    backend: OpenAICompatibleBackend,
    request_recorder: Callable[[dict[str, Any]], None] | None = None,
) -> tuple[list[ExtractedCandidate], dict[str, Any]]:
    """Extract parameter_spec/fault_code/performance_spec candidates from one rendered page image."""

    image_url = image_as_data_url(rendered_image_path)
    messages = build_visual_parameter_messages(
        image_url=image_url,
        page_no=page_no,
        equipment_class_id=equipment_class_id,
    )
    payload = _chat_payload(messages, backend)
    body = _post_json(backend, payload)
    if request_recorder:
        request_recorder({"request": payload, "response": body, "doc_id": doc_id, "page_no": page_no})
    parsed = parse_json_response_content(response_content_text(body))
    candidates = normalize_visual_candidates(parsed, page_no=page_no)
    return candidates, body.get("usage", {}) or {}


def normalize_visual_candidates(payload: dict[str, Any], *, page_no: int) -> list[ExtractedCandidate]:
    raw_candidates = payload.get("candidates") if isinstance(payload, dict) else None
    if not isinstance(raw_candidates, list):
        return []
    candidates = []
    for raw in raw_candidates:
        if not isinstance(raw, dict):
            continue
        candidate = _candidate_from_raw(raw, page_no=page_no)
        if candidate and is_reviewable_candidate(candidate):
            candidates.append(candidate)
    return candidates


def is_reviewable_candidate(candidate: ExtractedCandidate) -> bool:
    name = candidate.parameter_name.strip()
    evidence = candidate.evidence_quote.strip()
    if candidate.knowledge_object_type not in ALLOWED_TYPES:
        return False
    if len(name) < 2 or name.lower() in {"en", "cn", "na", "n/a", "none", "null"}:
        return False
    if not evidence or len(evidence) < 4:
        return False
    return True


def _candidate_from_raw(raw: dict[str, Any], *, page_no: int) -> ExtractedCandidate | None:
    knowledge_type = str(raw.get("knowledge_object_type") or raw.get("knowledge_type") or "parameter_spec").strip()
    parameter_name = str(raw.get("parameter_name") or raw.get("fault_code") or raw.get("title") or "").strip()
    evidence = str(raw.get("evidence_quote") or raw.get("evidence_text") or "").strip()
    if not parameter_name:
        return None

    structured_payload = {
        key: value
        for key, value in raw.items()
        if key not in {"knowledge_object_type", "knowledge_type", "confidence", "evidence_quote", "evidence_text", "page_no"}
        and value not in (None, "")
    }
    structured_payload.setdefault("parameter_name", parameter_name)
    structured_payload.setdefault("title", parameter_name)

    return ExtractedCandidate(
        knowledge_object_type=knowledge_type,
        parameter_name=parameter_name,
        structured_payload=structured_payload,
        evidence_quote=evidence,
        page_no=int(raw.get("page_no") or page_no),
        confidence=_float_or_default(raw.get("confidence"), 0.0),
        raw=raw,
    )


def _chat_payload(messages: list[dict[str, Any]], backend: OpenAICompatibleBackend) -> dict[str, Any]:
    payload = {
        "model": backend.model,
        "messages": messages,
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
        "stream": False,
    }
    for key, value in (backend.request_options or {}).items():
        if key in {"model", "messages"}:
            continue
        payload[key] = value
    payload.setdefault("max_completion_tokens", 6000)
    return payload


def _post_json(backend: OpenAICompatibleBackend, payload: dict[str, Any]) -> dict[str, Any]:
    client = _mimo_rate_limited_client()
    try:
        return client.call_sync(_post_json_once, backend, payload)
    except MaxRetriesExceeded as exc:
        raise RuntimeError(f"MiMo visual parameter request failed after retries: {exc}") from exc


def _post_json_once(backend: OpenAICompatibleBackend, payload: dict[str, Any]) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if backend.api_key:
        headers["Authorization"] = f"Bearer {backend.api_key}"
    req = request.Request(
        f"{backend.api_base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=backend.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError:
        raise
    except error.URLError as exc:
        raise RuntimeError(f"MiMo visual parameter request failed: {exc}") from exc


def _float_or_default(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


_MIMO_CLIENT: RateLimitedClient | None = None
_MIMO_CLIENT_LOCK = threading.Lock()


def _mimo_rate_limited_client() -> RateLimitedClient:
    global _MIMO_CLIENT
    with _MIMO_CLIENT_LOCK:
        if _MIMO_CLIENT is None:
            _MIMO_CLIENT = RateLimitedClient(
                max_concurrent=_env_int("LLM_MAX_CONCURRENT_MIMO", _env_int("LLM_MAX_CONCURRENT", 8)),
                max_rpm=_env_int("LLM_MAX_RPM_MIMO", 30),
                max_retries=_env_int("LLM_MAX_RETRIES_MIMO", _env_int("LLM_MAX_RETRIES", 5)),
            )
    return _MIMO_CLIENT


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default
