"""Optional LLM-assisted compiler backend for harder knowledge types."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request

from packages.compiler.contracts import DEFAULT_COMPILER_VERSION, build_compile_metadata
from packages.core.config import settings
from packages.db.models import ContentChunk, Document, DocumentPage

LLM_HARD_TYPES = (
    "parameter_spec",
    "maintenance_procedure",
    "application_guidance",
    "diagnostic_step",
    "symptom",
)
DEFAULT_LLM_ENABLED_TYPES = (
    "maintenance_procedure",
    "application_guidance",
)


@dataclass(frozen=True)
class ChunkContextWindow:
    chunk_ids: list[str]
    combined_text: str


@dataclass(frozen=True)
class OpenAICompatibleBackend:
    name: str
    api_base_url: str
    model: str
    api_key: str | None = None
    timeout_seconds: int = 30
    request_options: dict[str, Any] | None = None


def default_backend() -> OpenAICompatibleBackend | None:
    """Return the default compiler backend from settings."""

    if not settings.llm_compile_enabled or not settings.llm_model:
        return None
    return OpenAICompatibleBackend(
        name="default",
        api_base_url=settings.llm_api_base_url,
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        timeout_seconds=settings.llm_compile_timeout_seconds,
    )


def backend_from_dict(payload: dict[str, Any]) -> OpenAICompatibleBackend:
    """Build one OpenAI-compatible backend config from a dict."""

    model = str(payload.get("model") or "").strip()
    api_base_url = str(payload.get("api_base_url") or "").strip()
    if not model or not api_base_url:
        raise ValueError("backend config requires model and api_base_url")
    api_key = payload.get("api_key")
    api_key_env = payload.get("api_key_env")
    if not api_key and api_key_env:
        api_key = os.getenv(str(api_key_env))
    timeout_seconds = int(payload.get("timeout_seconds") or settings.llm_compile_timeout_seconds)
    request_options = payload.get("request_options")
    if request_options is not None and not isinstance(request_options, dict):
        raise ValueError("backend request_options must be an object")
    return OpenAICompatibleBackend(
        name=str(payload.get("name") or model),
        api_base_url=api_base_url,
        model=model,
        api_key=str(api_key) if api_key else None,
        timeout_seconds=timeout_seconds,
        request_options=dict(request_options or {}),
    )


def load_backend_configs(path: str | Path) -> list[OpenAICompatibleBackend]:
    """Load one backend config file."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = payload.get("backends") if isinstance(payload, dict) else payload
    if not isinstance(entries, list):
        raise ValueError("backend config file must be a list or an object with a backends list")
    return [backend_from_dict(item) for item in entries if isinstance(item, dict)]


def resolve_backend(
    *,
    config_path: str | Path | None = None,
    backend_name: str | None = None,
) -> OpenAICompatibleBackend | None:
    """Resolve one active backend from explicit args, settings-backed config, or direct settings."""

    active_config_path = config_path or settings.llm_backend_config_path
    active_backend_name = backend_name or settings.llm_backend_name
    if active_config_path:
        backends = load_backend_configs(active_config_path)
        if active_backend_name:
            for backend in backends:
                if backend.name == active_backend_name:
                    return backend
            raise ValueError(f"Backend '{active_backend_name}' not found in {active_config_path}")
        if len(backends) == 1:
            return backends[0]
        raise ValueError("Backend name is required when backend config contains multiple entries")
    return default_backend()


def default_enabled_llm_types() -> tuple[str, ...]:
    """Return the default enabled LLM types from settings."""

    values = [item.strip() for item in settings.llm_enabled_types.split(",") if item.strip()]
    if not values:
        values = list(DEFAULT_LLM_ENABLED_TYPES)
    return tuple(values)


def llm_compilation_enabled(backend: OpenAICompatibleBackend | None = None) -> bool:
    """Return whether the optional LLM compiler is configured."""

    active_backend = backend or default_backend()
    return bool(active_backend and active_backend.model and active_backend.api_base_url)


def build_context_window(
    rows: list[tuple[ContentChunk, DocumentPage, Document]],
    index: int,
    *,
    radius: int | None = None,
) -> ChunkContextWindow:
    """Build a compact chunk window around one source row."""

    window_radius = radius if radius is not None else settings.llm_compile_context_radius
    focus_doc_id = rows[index][0].doc_id
    start = max(0, index - window_radius)
    end = min(len(rows), index + window_radius + 1)
    selected = [row for row in rows[start:end] if row[0].doc_id == focus_doc_id]
    chunk_ids = [chunk.chunk_id for chunk, _, _ in selected]
    combined_text = "\n\n".join(chunk.cleaned_text for chunk, _, _ in selected if chunk.cleaned_text)
    return ChunkContextWindow(chunk_ids=chunk_ids, combined_text=combined_text)


def compile_llm_candidates(
    *,
    domain_id: str,
    chunk: ContentChunk,
    page: DocumentPage,
    document: Document,
    equipment_match: dict[str, Any],
    context_window: ChunkContextWindow,
    backend: OpenAICompatibleBackend | None = None,
    enabled_types: tuple[str, ...] | list[str] | None = None,
) -> list[dict[str, Any]]:
    """Compile optional LLM draft candidates for hard knowledge types."""

    active_backend = backend or default_backend()
    if not llm_compilation_enabled(active_backend):
        return []
    type_allowlist = tuple(enabled_types) if enabled_types is not None else default_enabled_llm_types()
    allowed_types = sorted(
        set(equipment_match["knowledge_anchors"]).intersection(LLM_HARD_TYPES).intersection(type_allowlist)
    )
    allowed_types = _context_allowed_types(allowed_types, chunk=chunk, page=page)
    if not allowed_types:
        return []

    prompt = _build_prompt(
        domain_id=domain_id,
        chunk=chunk,
        page=page,
        document=document,
        equipment_match=equipment_match,
        context_window=context_window,
        allowed_types=allowed_types,
    )
    try:
        response_payload = _request_json_completion(prompt, active_backend)
    except Exception:
        return []
    candidates = response_payload.get("candidates")
    if not isinstance(candidates, list):
        return []

    normalized = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        knowledge_type = str(item.get("knowledge_object_type") or "").strip()
        if knowledge_type not in allowed_types:
            continue
        canonical_key_candidate = str(item.get("canonical_key_candidate") or "").strip()
        structured_payload_candidate = item.get("structured_payload_candidate")
        if not canonical_key_candidate or not isinstance(structured_payload_candidate, dict):
            continue
        canonical_key_candidate = normalize_llm_canonical_key(
            canonical_key_candidate,
            domain_id=domain_id,
            equipment_class_id=equipment_match["equipment_class_id"],
            knowledge_object_type=knowledge_type,
            fallback_text=chunk.text_excerpt or chunk.cleaned_text,
        )
        try:
            confidence_score = float(item.get("confidence_score", 0.72))
        except (TypeError, ValueError):
            confidence_score = 0.72
        rationale = str(item.get("rationale") or "llm draft from constrained chunk window").strip()
        normalized.append(
            {
                "knowledge_object_type": knowledge_type,
                "canonical_key_candidate": canonical_key_candidate,
                "structured_payload_candidate": structured_payload_candidate,
                "confidence_score": round(max(0.0, min(confidence_score, 0.95)), 3),
                "knowledge_signal": {
                    "detection_method": "llm_compile",
                    "allowed_types": allowed_types,
                },
                "compile_metadata": build_compile_metadata(
                    "llm_compiler",
                    version=DEFAULT_COMPILER_VERSION,
                    rationale=rationale,
                    source_span_ids=context_window.chunk_ids,
                    extra={"model": active_backend.model, "backend_name": active_backend.name},
                ),
            }
        )
    return normalized


def _build_prompt(
    *,
    domain_id: str,
    chunk: ContentChunk,
    page: DocumentPage,
    document: Document,
    equipment_match: dict[str, Any],
    context_window: ChunkContextWindow,
    allowed_types: list[str],
) -> list[dict[str, str]]:
    system_prompt = (
        "You are compiling industrial authority candidates for KnowFabric. "
        "Return only strict JSON with shape "
        '{"candidates":[{"knowledge_object_type":"","canonical_key_candidate":"","structured_payload_candidate":{},"confidence_score":0.0,"rationale":""}]}. '
        "Use only the provided evidence. Do not invent applicability, brands, model families, or facts not grounded in the text. "
        "Prefer no candidate over a weak candidate. "
        "canonical_key_candidate must be machine-friendly: lowercase, stable, no spaces, and preferably namespaced like "
        "'hvac:ahu:maintenance:inspect_and_calibrate_airflow'. Never return title-cased or sentence-like keys."
    )
    user_prompt = json.dumps(
        {
            "task": "compile_hard_type_candidates",
            "domain_id": domain_id,
            "document_name": document.file_name,
            "page_type": page.page_type,
            "chunk_type": chunk.chunk_type,
            "equipment_class_id": equipment_match["equipment_class_id"],
            "equipment_class_key": equipment_match["equipment_class_key"],
            "equipment_label": equipment_match["label"],
            "allowed_knowledge_types": allowed_types,
            "focus_chunk_id": chunk.chunk_id,
            "focus_chunk_excerpt": chunk.text_excerpt,
            "focus_chunk_text": chunk.cleaned_text,
            "context_chunk_ids": context_window.chunk_ids,
            "context_window_text": context_window.combined_text,
            "rules": [
                "Use only supported knowledge types.",
                "For parameter_spec, structured_payload_candidate should include parameter_name and any verbatim value, unit, range_min, range_max, default_value, or description found in the evidence.",
                "For parameter_spec, do not infer units, ranges, defaults, limits, or descriptions that are not visible in the source text.",
                "canonical_key_candidate must be lowercase and machine-friendly with underscores or colon namespaces only.",
                "Do not use spaces, punctuation-heavy titles, or prose as canonical_key_candidate.",
                "structured_payload_candidate must be a JSON object.",
                "If the evidence is insufficient, return an empty candidates array.",
            ],
        },
        ensure_ascii=False,
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _context_allowed_types(
    allowed_types: list[str],
    *,
    chunk: ContentChunk,
    page: DocumentPage,
) -> list[str]:
    """Restrict hard-type compilation to contexts likely to be valid."""

    normalized_text = _normalize_chunk_text(chunk)
    filtered = []
    for knowledge_type in allowed_types:
        if knowledge_type == "parameter_spec":
            if _is_llm_parameter_context(normalized_text, chunk.chunk_type, page.page_type):
                filtered.append(knowledge_type)
            continue
        if knowledge_type == "application_guidance":
            if _is_llm_application_context(normalized_text, chunk.chunk_type, page.page_type):
                filtered.append(knowledge_type)
            continue
        if knowledge_type == "maintenance_procedure":
            if _is_llm_maintenance_context(normalized_text, chunk.chunk_type, page.page_type):
                filtered.append(knowledge_type)
            continue
        if knowledge_type == "diagnostic_step":
            if _is_llm_diagnostic_context(normalized_text, chunk.chunk_type, page.page_type):
                filtered.append(knowledge_type)
            continue
        if knowledge_type == "symptom":
            if _is_llm_symptom_context(normalized_text, chunk.chunk_type, page.page_type):
                filtered.append(knowledge_type)
            continue
        filtered.append(knowledge_type)
    return filtered


def _normalize_chunk_text(chunk: ContentChunk) -> str:
    text = " ".join(filter(None, [chunk.cleaned_text, chunk.text_excerpt]))
    return _slugify_part(text).replace("_", " ")


def _combined_type_text(chunk_type: str, page_type: str | None) -> str:
    return " ".join(filter(None, [chunk_type.lower(), (page_type or "").lower()]))


def _is_llm_parameter_context(normalized_text: str, chunk_type: str, page_type: str | None) -> bool:
    combined_type = _combined_type_text(chunk_type, page_type)
    if any(token in combined_type for token in ("fault", "alarm", "maintenance", "commission", "wiring")):
        return False
    if any(token in combined_type for token in ("parameter", "spec", "setting")):
        return True
    parameter_markers = (
        "parameter",
        "setting",
        "setpoint",
        "default",
        "range",
        "limit",
        "threshold",
        "参数",
        "设定",
        "默认",
        "范围",
        "限值",
        "阈值",
    )
    has_value = bool(re.search(r"\d+(?:\.\d+)?\s*(?:kw|rt|hz|v|a|m3/h|l/s|c|°c|%)", normalized_text))
    return has_value and any(marker in normalized_text for marker in parameter_markers)


def _is_llm_application_context(normalized_text: str, chunk_type: str, page_type: str | None) -> bool:
    combined_type = _combined_type_text(chunk_type, page_type)
    if any(token in combined_type for token in ("spec", "parameter", "fault", "maintenance", "commission", "wiring", "checklist")):
        return False
    if any(token in combined_type for token in ("guidance", "application", "sequence")):
        return True
    strong_markers = (
        "operate together",
        "same mode",
        "use for",
        "recommended for",
        "suitable for",
        "control applications",
        "control application",
        "sequence",
        "运行模式",
        "适用",
        "应用",
        "用于",
    )
    return any(marker in normalized_text for marker in strong_markers)


def _is_llm_maintenance_context(normalized_text: str, chunk_type: str, page_type: str | None) -> bool:
    combined_type = _combined_type_text(chunk_type, page_type)
    if any(token in combined_type for token in ("fault", "parameter")):
        return False
    if any(token in combined_type for token in ("maintenance", "procedure")):
        return True
    strong_markers = (
        "inspect",
        "calibrate",
        "preventive maintenance",
        "maintenance plan",
        "clean",
        "replace",
        "维护",
        "保养",
        "检查",
    )
    return any(marker in normalized_text for marker in strong_markers)


def _is_llm_diagnostic_context(normalized_text: str, chunk_type: str, page_type: str | None) -> bool:
    combined_type = _combined_type_text(chunk_type, page_type)
    if any(token in combined_type for token in ("fault", "parameter")):
        return False
    diagnostic_markers = ("inspect", "check", "verify", "diagnose", "确认", "检查", "排查")
    return any(marker in normalized_text for marker in diagnostic_markers)


def _is_llm_symptom_context(normalized_text: str, chunk_type: str, page_type: str | None) -> bool:
    combined_type = _combined_type_text(chunk_type, page_type)
    if any(token in combined_type for token in ("fault", "alarm", "symptom")):
        return True
    symptom_markers = ("symptom", "warning", "alarm", "trip", "故障", "报警", "症状")
    return any(marker in normalized_text for marker in symptom_markers)


def _request_json_completion(
    messages: list[dict[str, str]],
    backend: OpenAICompatibleBackend,
) -> dict[str, Any]:
    payload = _chat_completion_payload(messages, backend)
    base_url = backend.api_base_url.rstrip("/")
    headers = {
        "Content-Type": "application/json",
    }
    if backend.api_key:
        headers["Authorization"] = f"Bearer {backend.api_key}"
    req = request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=backend.timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
    except error.URLError as exc:
        raise RuntimeError(f"LLM compile request failed: {exc}") from exc

    content = (
        body.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )
    if isinstance(content, list):
        content = "".join(str(part.get("text", "")) for part in content if isinstance(part, dict))
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("LLM compile returned empty content")
    return json.loads(content)


def _chat_completion_payload(
    messages: list[dict[str, str]],
    backend: OpenAICompatibleBackend,
) -> dict[str, Any]:
    payload = {
        "model": backend.model,
        "temperature": 0.0,
        "messages": messages,
        "response_format": {"type": "json_object"},
    }
    for key, value in (backend.request_options or {}).items():
        if key in {"model", "messages"}:
            continue
        payload[key] = value
    return payload


def normalize_llm_canonical_key(
    raw_key: str,
    *,
    domain_id: str,
    equipment_class_id: str,
    knowledge_object_type: str,
    fallback_text: str,
) -> str:
    """Normalize one LLM-produced canonical key into a stable machine-friendly format."""

    raw = raw_key.strip()
    if not raw:
        raw = fallback_text
    type_prefix = _knowledge_type_prefix(knowledge_object_type)
    if ":" in raw:
        parts = [_slugify_part(part) for part in raw.split(":") if _slugify_part(part)]
        domain_slug = _slugify_part(domain_id)
        equipment_slug = _slugify_part(equipment_class_id)
        if len(parts) >= 4:
            return ":".join(parts[:3] + ["_".join(parts[3:])])
        if len(parts) == 3 and parts[0] == domain_slug and parts[1] == equipment_slug and parts[2] != type_prefix:
            return ":".join([parts[0], parts[1], type_prefix, parts[2]])
        if len(parts) == 3:
            return ":".join(parts)
        if len(parts) == 2 and parts[0] == domain_slug:
            return ":".join([parts[0], parts[1], type_prefix, _slugify_part(fallback_text)])
        if len(parts) == 2:
            return ":".join([parts[0], parts[1], type_prefix, _slugify_part(fallback_text)])
        if len(parts) == 1:
            return f"{domain_slug}:{equipment_slug}:{type_prefix}:{parts[0]}"
    slug = _slugify_part(raw)
    if not slug:
        slug = _slugify_part(fallback_text)
    return f"{_slugify_part(domain_id)}:{_slugify_part(equipment_class_id)}:{type_prefix}:{slug}"


def _knowledge_type_prefix(knowledge_object_type: str) -> str:
    mapping = {
        "parameter_spec": "parameter",
        "maintenance_procedure": "maintenance",
        "application_guidance": "application",
        "diagnostic_step": "diagnostic",
        "symptom": "symptom",
    }
    return mapping.get(knowledge_object_type, _slugify_part(knowledge_object_type))


def _slugify_part(value: str) -> str:
    collapsed = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return collapsed
