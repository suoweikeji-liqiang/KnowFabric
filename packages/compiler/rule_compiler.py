"""Rule-based compiler backend for chunk review candidates."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from packages.compiler.contracts import DEFAULT_COMPILER_VERSION, build_compile_metadata
from packages.compiler.equipment_matcher import load_document_profile_map, normalize_text
from packages.db.models import ContentChunk, Document, DocumentPage

FAULT_CONTEXT_MARKERS = (
    "fault",
    "alarm",
    "warning",
    "error",
    "protection",
    "trip",
    "故障",
    "报警",
    "保护",
    "告警",
)
PARAMETER_CONTEXT_MARKERS = (
    "parameter",
    "setting",
    "default",
    "threshold",
    "group",
    "参数",
    "设定",
    "阈值",
    "默认",
)
PERFORMANCE_CONTEXT_MARKERS = (
    "rated",
    "nominal",
    "capacity",
    "efficiency",
    "cop",
    "eer",
    "performance",
    "specification",
    "rating",
    "output",
    "额定",
    "性能",
    "效率",
    "能力",
)
PERFORMANCE_CATEGORY_KEYWORDS = {
    "capacity": ("capacity", "cooling capacity", "heating capacity", "output", "rt", "kw", "能力", "制冷量"),
    "efficiency": ("efficiency", "cop", "eer", "kw/rt", "效率"),
    "temperature": ("temperature", "leaving temp", "approach", "°c", "c", "温度"),
    "flow": ("flow", "water flow", "air flow", "m3/h", "l/s", "流量"),
}
COMMISSIONING_CONTEXT_MARKERS = (
    "commission",
    "startup",
    "start-up",
    "getting started",
    "backup settings",
    "upload settings",
    "调试",
    "启动",
    "设置备份",
    "上传变频器设置",
)
WIRING_CONTEXT_MARKERS = (
    "wiring",
    "terminal",
    "cable",
    "shield",
    "ground",
    "modbus",
    "bacnet",
    "rs485",
    "communication port",
    "接线",
    "端子",
    "屏蔽",
    "接地",
    "通讯",
)
APPLICATION_CONTEXT_MARKERS = (
    "application",
    "pump",
    "fan",
    "flow",
    "pressure",
    "hvac",
    "应用",
    "风机",
    "水泵",
    "流量",
    "压力",
)
MAINTENANCE_CONTEXT_MARKERS = (
    "maintenance",
    "service",
    "procedure",
    "clean",
    "wash",
    "inspect",
    "check",
    "replace",
    "lubricate",
    "maintain",
    "guide",
    "维护",
    "保养",
    "检查",
    "清洗",
    "清洁",
)
MAINTENANCE_TASK_KEYWORDS = {
    "cleaning": ("clean", "wash", "清洗", "清洁"),
    "inspection": ("inspect", "check", "检查"),
    "replacement": ("replace", "更换"),
    "lubrication": ("lubricate", "润滑"),
}
STRONG_MAINTENANCE_MARKERS = (
    "clean",
    "wash",
    "replace",
    "lubricate",
    "maintain",
    "regularly",
    "periodic",
    "清洗",
    "清洁",
    "更换",
    "润滑",
    "保养",
)
DIAGNOSTIC_STEP_MARKERS = (
    "check",
    "inspect",
    "verify",
    "increase",
    "decrease",
    "vent",
    "排气",
    "检查",
    "确认",
)
FAULT_CODE_PATTERN = re.compile(r"\b([A-Z]\d[A-Z0-9]{1,6})\b", re.IGNORECASE)
NUMERIC_FAULT_CODE_PATTERN = re.compile(r"\b(\d{2,4})\b")
PARAMETER_CODE_PATTERN = re.compile(r"\b(p\d{3,5})\b", re.IGNORECASE)
VALUE_WITH_UNIT_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:rt|kw|cop|eer|kw/rt|m3/h|l/s|°c|c|%)\b",
    re.IGNORECASE,
)
PREFIXED_VALUE_PATTERN = re.compile(
    r"\b(?:cop|eer)\s*\d+(?:\.\d+)?\b",
    re.IGNORECASE,
)


def short_text(text: str, limit: int = 220) -> str:
    """Return a compact preview for one evidence block."""

    collapsed = re.sub(r"\s+", " ", text.strip())
    if len(collapsed) <= limit:
        return collapsed
    return f"{collapsed[: limit - 3]}..."


def stable_candidate_id(*parts: str) -> str:
    """Generate one stable candidate id from deterministic seeds."""

    digest = hashlib.sha1("::".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"cand_{digest}"


def _has_context(markers: tuple[str, ...], *texts: str) -> bool:
    combined = " ".join(texts)
    return any(marker in combined for marker in markers)


def _is_parameter_context(normalized_chunk: str, chunk_type: str, page_type: str | None) -> bool:
    return _has_context(PARAMETER_CONTEXT_MARKERS, normalized_chunk, chunk_type, page_type or "")


def _is_performance_context(normalized_chunk: str, chunk_type: str, page_type: str | None) -> bool:
    if _has_context(("maintenance", "fault", "alarm"), chunk_type, page_type or ""):
        return False
    return _has_context(PERFORMANCE_CONTEXT_MARKERS, normalized_chunk, chunk_type, page_type or "")


def _is_commissioning_context(normalized_chunk: str, chunk_type: str, page_type: str | None) -> bool:
    return _has_context(COMMISSIONING_CONTEXT_MARKERS, normalized_chunk, chunk_type, page_type or "")


def _is_wiring_context(normalized_chunk: str, chunk_type: str, page_type: str | None) -> bool:
    return _has_context(WIRING_CONTEXT_MARKERS, normalized_chunk, chunk_type, page_type or "")


def _is_application_context(normalized_chunk: str, chunk_type: str, page_type: str | None) -> bool:
    if _is_fault_context(normalized_chunk, chunk_type, page_type):
        return False
    return _has_context(APPLICATION_CONTEXT_MARKERS, normalized_chunk, chunk_type, page_type or "")


def _is_fault_context(normalized_chunk: str, chunk_type: str, page_type: str | None) -> bool:
    typed_fault = _has_context(("fault", "alarm"), chunk_type, page_type or "")
    if typed_fault:
        return True
    if _has_context(("parameter",), chunk_type, page_type or ""):
        return False
    return _has_context(FAULT_CONTEXT_MARKERS, normalized_chunk)


def _candidate_confidence(base: float, equipment_confidence: float, context_bonus: float) -> float:
    return round(min(base + context_bonus + (equipment_confidence - 0.6) * 0.25, 0.99), 3)


def _slug_from_text(text: str, limit: int = 6) -> str:
    tokens = re.findall(r"[a-z0-9]+", normalize_text(text))
    return "_".join(tokens[:limit]) or "candidate"


def _infer_maintenance_task(text: str) -> str:
    normalized = normalize_text(text)
    for task_type, keywords in MAINTENANCE_TASK_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return task_type
    return "maintenance"


def _infer_performance_category(text: str) -> str:
    normalized = normalize_text(text)
    for category, keywords in PERFORMANCE_CATEGORY_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return category
    return "performance"


def _infer_application_type(text: str) -> str:
    normalized = normalize_text(text)
    if "pump" in normalized and "fan" in normalized:
        return "pump_fan"
    if "pump" in normalized or "水泵" in normalized:
        return "pump"
    if "fan" in normalized or "风机" in normalized:
        return "fan"
    if "flow" in normalized or "流量" in normalized:
        return "flow"
    return "application"


def _procedure_context_text(chunk_type: str, page_type: str | None, normalized_chunk: str) -> str:
    return " ".join(filter(None, [chunk_type, page_type or "", normalized_chunk]))


def _is_procedure_context(normalized_chunk: str, chunk_type: str, page_type: str | None) -> bool:
    return _has_context(MAINTENANCE_CONTEXT_MARKERS, _procedure_context_text(chunk_type, page_type, normalized_chunk))


def _detect_parameter_candidates(
    normalized_chunk: str,
    chunk_type: str,
    page_type: str | None,
    equipment_confidence: float,
) -> list[dict[str, Any]]:
    if not _is_parameter_context(normalized_chunk, chunk_type, page_type):
        return []
    candidates = []
    for token in sorted({match.lower() for match in PARAMETER_CODE_PATTERN.findall(normalized_chunk)}):
        candidates.append(
            {
                "knowledge_object_type": "parameter_spec",
                "canonical_key_candidate": token,
                "structured_payload_candidate": {"parameter_name": token},
                "confidence_score": _candidate_confidence(0.8, equipment_confidence, 0.05),
                "knowledge_signal": {"matched_token": token, "detection_method": "parameter_regex"},
                "compile_metadata": build_compile_metadata(
                    "rule_compiler",
                    version=DEFAULT_COMPILER_VERSION,
                    rationale="parameter code regex matched in chunk text",
                ),
            }
        )
    return candidates


def _detect_performance_candidates(
    normalized_chunk: str,
    display_text: str,
    chunk_type: str,
    page_type: str | None,
    equipment_confidence: float,
) -> list[dict[str, Any]]:
    if not _is_performance_context(normalized_chunk, chunk_type, page_type):
        return []
    category = _infer_performance_category(display_text)
    rated_value = None
    match = VALUE_WITH_UNIT_PATTERN.search(display_text)
    if match:
        rated_value = match.group(0)
    else:
        prefixed_match = PREFIXED_VALUE_PATTERN.search(display_text)
        if prefixed_match:
            rated_value = prefixed_match.group(0).upper()
    structured_payload = {
        "parameter_name": _slug_from_text(display_text),
        "parameter_category": category,
    }
    if rated_value:
        structured_payload["rated_value"] = rated_value
    return [
        {
            "knowledge_object_type": "performance_spec",
            "canonical_key_candidate": f"{category}_{_slug_from_text(display_text)}",
            "structured_payload_candidate": structured_payload,
            "confidence_score": _candidate_confidence(0.79, equipment_confidence, 0.04),
            "knowledge_signal": {"matched_category": category, "detection_method": "performance_context"},
            "compile_metadata": build_compile_metadata(
                "rule_compiler",
                version=DEFAULT_COMPILER_VERSION,
                rationale="performance context markers and value-with-unit parsing matched",
            ),
        }
    ]


def _detect_commissioning_candidates(
    normalized_chunk: str,
    display_text: str,
    chunk_type: str,
    page_type: str | None,
    equipment_confidence: float,
) -> list[dict[str, Any]]:
    if not _is_commissioning_context(normalized_chunk, chunk_type, page_type):
        return []
    if _is_wiring_context(normalized_chunk, chunk_type, page_type):
        return []
    return [
        {
            "knowledge_object_type": "commissioning_step",
            "canonical_key_candidate": _slug_from_text(display_text),
            "structured_payload_candidate": {
                "step": display_text,
                "commissioning_phase": "startup",
            },
            "confidence_score": _candidate_confidence(0.78, equipment_confidence, 0.03),
            "knowledge_signal": {"detection_method": "commissioning_context"},
            "compile_metadata": build_compile_metadata(
                "rule_compiler",
                version=DEFAULT_COMPILER_VERSION,
                rationale="commissioning/startup context markers matched",
            ),
        }
    ]


def _detect_wiring_candidates(
    normalized_chunk: str,
    display_text: str,
    chunk_type: str,
    page_type: str | None,
    equipment_confidence: float,
) -> list[dict[str, Any]]:
    if not _is_wiring_context(normalized_chunk, chunk_type, page_type):
        return []
    topic = "wiring"
    if "modbus" in normalized_chunk or "bacnet" in normalized_chunk or "rs485" in normalized_chunk:
        topic = "communication_wiring"
    elif "shield" in normalized_chunk or "ground" in normalized_chunk or "接地" in normalized_chunk:
        topic = "shield_grounding"
    elif "terminal" in normalized_chunk or "端子" in normalized_chunk:
        topic = "terminal_connection"
    return [
        {
            "knowledge_object_type": "wiring_guidance",
            "canonical_key_candidate": f"{topic}_{_slug_from_text(display_text)}",
            "structured_payload_candidate": {
                "wiring_topic": topic,
                "guidance": display_text,
            },
            "confidence_score": _candidate_confidence(0.77, equipment_confidence, 0.03),
            "knowledge_signal": {"matched_topic": topic, "detection_method": "wiring_context"},
            "compile_metadata": build_compile_metadata(
                "rule_compiler",
                version=DEFAULT_COMPILER_VERSION,
                rationale="wiring/terminal/shield markers matched",
            ),
        }
    ]


def _detect_application_guidance_candidates(
    normalized_chunk: str,
    display_text: str,
    chunk_type: str,
    page_type: str | None,
    equipment_confidence: float,
) -> list[dict[str, Any]]:
    if not _is_application_context(normalized_chunk, chunk_type, page_type):
        return []
    application_type = _infer_application_type(display_text)
    return [
        {
            "knowledge_object_type": "application_guidance",
            "canonical_key_candidate": f"{application_type}_{_slug_from_text(display_text)}",
            "structured_payload_candidate": {
                "application_type": application_type,
                "guidance": display_text,
            },
            "confidence_score": _candidate_confidence(0.76, equipment_confidence, 0.03),
            "knowledge_signal": {"matched_application_type": application_type, "detection_method": "application_context"},
            "compile_metadata": build_compile_metadata(
                "rule_compiler",
                version=DEFAULT_COMPILER_VERSION,
                rationale="application domain markers matched",
            ),
        }
    ]


def _detect_fault_candidates(
    normalized_chunk: str,
    chunk_type: str,
    page_type: str | None,
    equipment_confidence: float,
) -> list[dict[str, Any]]:
    if not _is_fault_context(normalized_chunk, chunk_type, page_type):
        return []
    alphanumeric = {
        match.upper()
        for match in FAULT_CODE_PATTERN.findall(normalized_chunk)
        if not match.lower().startswith("p")
    }
    numeric = set(NUMERIC_FAULT_CODE_PATTERN.findall(normalized_chunk))
    tokens = sorted(alphanumeric) + sorted(numeric)
    candidates = []
    for token in tokens:
        candidates.append(
            {
                "knowledge_object_type": "fault_code",
                "canonical_key_candidate": token,
                "structured_payload_candidate": {"fault_code": token},
                "confidence_score": _candidate_confidence(0.85, equipment_confidence, 0.04),
                "knowledge_signal": {"matched_token": token, "detection_method": "fault_regex"},
                "compile_metadata": build_compile_metadata(
                    "rule_compiler",
                    version=DEFAULT_COMPILER_VERSION,
                    rationale="fault code regex matched in fault context",
                ),
            }
        )
    return candidates


def _detect_maintenance_candidates(
    normalized_chunk: str,
    display_text: str,
    chunk_type: str,
    page_type: str | None,
    equipment_confidence: float,
) -> list[dict[str, Any]]:
    if not _is_procedure_context(normalized_chunk, chunk_type, page_type):
        return []
    if _has_context(DIAGNOSTIC_STEP_MARKERS, normalized_chunk) and not _has_context(STRONG_MAINTENANCE_MARKERS, normalized_chunk):
        return []
    task_type = _infer_maintenance_task(normalized_chunk)
    return [
        {
            "knowledge_object_type": "maintenance_procedure",
            "canonical_key_candidate": f"{task_type}_{_slug_from_text(display_text)}",
            "structured_payload_candidate": {
                "maintenance_task": task_type,
                "task_type": task_type,
                "steps": [display_text],
            },
            "confidence_score": _candidate_confidence(0.75, equipment_confidence, 0.03),
            "knowledge_signal": {"matched_task_type": task_type, "detection_method": "procedure_context"},
            "compile_metadata": build_compile_metadata(
                "rule_compiler",
                version=DEFAULT_COMPILER_VERSION,
                rationale="maintenance procedure context markers matched",
            ),
        }
    ]


def _detect_diagnostic_step_candidates(
    normalized_chunk: str,
    display_text: str,
    chunk_type: str,
    page_type: str | None,
    equipment_confidence: float,
) -> list[dict[str, Any]]:
    if not _is_procedure_context(normalized_chunk, chunk_type, page_type):
        return []
    if not _has_context(DIAGNOSTIC_STEP_MARKERS, normalized_chunk):
        return []
    task_type = _infer_maintenance_task(normalized_chunk)
    return [
        {
            "knowledge_object_type": "diagnostic_step",
            "canonical_key_candidate": f"{task_type}_{_slug_from_text(display_text)}",
            "structured_payload_candidate": {
                "task_type": task_type,
                "step": display_text,
            },
            "confidence_score": _candidate_confidence(0.74, equipment_confidence, 0.03),
            "knowledge_signal": {"matched_task_type": task_type, "detection_method": "diagnostic_procedure_context"},
            "compile_metadata": build_compile_metadata(
                "rule_compiler",
                version=DEFAULT_COMPILER_VERSION,
                rationale="diagnostic verb markers matched in procedure context",
            ),
        }
    ]


def detect_rule_knowledge_candidates(
    chunk: ContentChunk,
    page: DocumentPage,
    equipment_match: dict[str, Any],
) -> list[dict[str, Any]]:
    """Detect rule-based knowledge candidates for one chunk."""

    display_text = chunk.text_excerpt or short_text(chunk.cleaned_text)
    normalized_chunk = normalize_text(" ".join(filter(None, [chunk.cleaned_text, chunk.text_excerpt])))
    knowledge_anchors = set(equipment_match["knowledge_anchors"])
    domain_id = equipment_match["equipment_class_key"].split(":", 1)[0]
    preferred = load_document_profile_map(domain_id).get(page.page_type or "")
    if preferred:
        knowledge_anchors &= preferred

    candidates = []
    if "parameter_spec" in knowledge_anchors:
        candidates.extend(
            _detect_parameter_candidates(
                normalized_chunk,
                chunk.chunk_type,
                page.page_type,
                equipment_match["confidence"],
            )
        )
    if "fault_code" in knowledge_anchors:
        candidates.extend(
            _detect_fault_candidates(
                normalized_chunk,
                chunk.chunk_type,
                page.page_type,
                equipment_match["confidence"],
            )
        )
    if "performance_spec" in knowledge_anchors:
        candidates.extend(
            _detect_performance_candidates(
                normalized_chunk,
                display_text,
                chunk.chunk_type,
                page.page_type,
                equipment_match["confidence"],
            )
        )
    if "commissioning_step" in knowledge_anchors:
        candidates.extend(
            _detect_commissioning_candidates(
                normalized_chunk,
                display_text,
                chunk.chunk_type,
                page.page_type,
                equipment_match["confidence"],
            )
        )
    if "wiring_guidance" in knowledge_anchors:
        candidates.extend(
            _detect_wiring_candidates(
                normalized_chunk,
                display_text,
                chunk.chunk_type,
                page.page_type,
                equipment_match["confidence"],
            )
        )
    if "application_guidance" in knowledge_anchors:
        candidates.extend(
            _detect_application_guidance_candidates(
                normalized_chunk,
                display_text,
                chunk.chunk_type,
                page.page_type,
                equipment_match["confidence"],
            )
        )
    if "maintenance_procedure" in knowledge_anchors:
        candidates.extend(
            _detect_maintenance_candidates(
                normalized_chunk,
                display_text,
                chunk.chunk_type,
                page.page_type,
                equipment_match["confidence"],
            )
        )
    if "diagnostic_step" in knowledge_anchors:
        candidates.extend(
            _detect_diagnostic_step_candidates(
                normalized_chunk,
                display_text,
                chunk.chunk_type,
                page.page_type,
                equipment_match["confidence"],
            )
        )
    return candidates
