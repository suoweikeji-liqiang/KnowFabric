"""MiMo visual-native extraction — page image → DocumentPageImageV2 rows.

Uses MiMo multimodal API to analyze rendered PDF page images and produce
structured visual evidence (image_type, entities, relationships, etc.).
"""

from __future__ import annotations

import base64
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Callable
from urllib import error, request

from packages.compiler.llm_compiler import OpenAICompatibleBackend, resolve_backend

DEFAULT_PAGE_TYPES = (
    "text_scan",
    "parameter_table",
    "fault_table",
    "wiring_diagram",
    "system_schematic",
    "controller_screen",
    "nameplate",
    "equipment_structure",
    "other",
)

PAGE_IMAGE_ID_PREFIX = "pimg"
TOKEN_BUDGET_CAP = 8.4e8


class TokenBudgetExceeded(Exception):
    pass


def image_as_data_url(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def build_messages(image_url: str) -> list[dict[str, Any]]:
    system = (
        "You inspect HVAC manual page images for visual evidence. "
        "This is not OCR-only. Classify the visible page/region and extract "
        "only clearly visible visual facts. For diagrams, focus on components, "
        "terminals, signals, connections, and spatial relationships. "
        "If a relationship is uncertain, put it in summary, not relationships. "
        "Reply with strict JSON only."
    )
    user = (
        "Analyze this HVAC manual page as a visual evidence anchor. Return JSON with keys: "
        "page_type, summary, visual_entities, visual_relationships, useful_for_knowledge_types, "
        "ocr_text_if_useful, uncertainty_notes, confidence. "
        f"page_type must be one of: {', '.join(DEFAULT_PAGE_TYPES)}. "
        "visual_entities should be short objects with type and label. "
        "visual_relationships should be short objects with from, relation, to "
        "only when the connection or relationship is visibly supported."
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


def _response_text(body: dict[str, Any]) -> str:
    content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    if isinstance(content, list):
        return "".join(
            str(part.get("text", "")) for part in content if isinstance(part, dict)
        ).strip()
    return str(content).strip()


def _parse_json_or_empty(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


DEFAULT_MIMO_BACKEND = "mimo-v2-omni"


def call_mimo(
    image_url: str,
    backend: OpenAICompatibleBackend,
    *,
    temperature: float = 0.0,
    timeout_seconds: int = 60,
    max_tokens: int = 60000,
    request_recorder: Callable[[dict[str, Any]], None] | None = None,
) -> tuple[dict[str, Any], str, dict[str, Any]]:
    """Call MiMo multimodal API for one page image.

    Returns (parsed_body, raw_text, usage).
    """
    payload = {
        "model": backend.model,
        "messages": build_messages(image_url),
        "temperature": temperature,
        "max_completion_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "stream": False,
    }
    headers = {
        "Content-Type": "application/json",
    }
    if backend.api_key:
        headers["Authorization"] = f"Bearer {backend.api_key}"

    base_url = backend.api_base_url.rstrip("/")
    req = request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
    except error.URLError as exc:
        raise RuntimeError(f"MiMo request failed: {exc}") from exc

    if request_recorder:
        request_recorder({"request": payload, "response": body})

    text = _response_text(body)
    parsed = _parse_json_or_empty(text)
    usage = body.get("usage", {})
    return parsed, text, usage


def page_image_id(doc_id: str, page_no: int) -> str:
    raw = f"{doc_id}:{page_no}"
    return f"{PAGE_IMAGE_ID_PREFIX}_{hashlib.sha1(raw.encode()).hexdigest()[:14]}"


def extract_visual_evidence(
    *,
    doc_id: str,
    page_id: str,
    page_no: int,
    image_path: Path,
    backend: OpenAICompatibleBackend,
    request_recorder: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Analyze one rendered page image with MiMo and return a DocumentPageImageV2 row dict.

    Args:
        doc_id: Document ID.
        page_id: DocumentPage ID.
        page_no: Page number.
        image_path: Path to rendered PNG file.
        backend: MiMo backend config.
        request_recorder: Optional callback for audit logging.

    Returns:
        Dict ready for DocumentPageImageV2 insertion.
    """
    image_url = image_as_data_url(image_path)
    parsed, raw_text, usage = call_mimo(
        image_url,
        backend,
        timeout_seconds=backend.timeout_seconds,
        request_recorder=request_recorder,
    )

    image_type = parsed.get("page_type", "other")
    if image_type not in DEFAULT_PAGE_TYPES:
        image_type = "other"

    entities = parsed.get("visual_entities")
    if isinstance(entities, list):
        entities = [e for e in entities if isinstance(e, dict)]

    relationships = parsed.get("visual_relationships")
    if isinstance(relationships, list):
        relationships = [r for r in relationships if isinstance(r, dict)]

    useful_types = parsed.get("useful_for_knowledge_types")
    if not isinstance(useful_types, list):
        useful_types = []

    return {
        "page_image_id": page_image_id(doc_id, page_no),
        "doc_id": doc_id,
        "page_id": page_id,
        "page_no": page_no,
        "image_path": str(image_path),
        "image_type": image_type,
        "summary": parsed.get("summary", "") or "",
        "ocr_text": parsed.get("ocr_text_if_useful"),
        "vl_summary": parsed.get("summary", "") or "",
        "vl_entities_json": entities,
        "vl_relationships_json": relationships,
        "useful_for_knowledge_types": useful_types,
        "uncertainty_notes": parsed.get("uncertainty_notes"),
        "vl_model": backend.model,
        "confidence": parsed.get("confidence"),
    }


class CumulativeTokenCounter:
    """Track cumulative token usage across MiMo calls. Raises TokenBudgetExceeded at cap."""

    def __init__(self, cap: int = int(TOKEN_BUDGET_CAP)):
        self.cap = cap
        self.total_input: int = 0
        self.total_output: int = 0

    @property
    def total_tokens(self) -> int:
        return self.total_input + self.total_output

    def add(self, usage: dict[str, Any]) -> None:
        self.total_input += usage.get("prompt_tokens", 0) or usage.get("input_tokens", 0) or 0
        self.total_output += usage.get("completion_tokens", 0) or usage.get("output_tokens", 0) or 0
        if self.total_tokens > self.cap:
            raise TokenBudgetExceeded(
                f"Cumulative tokens {self.total_tokens:,} exceed budget cap {self.cap:,}"
            )

    def summary(self) -> dict[str, Any]:
        return {
            "total_input_tokens": self.total_input,
            "total_output_tokens": self.total_output,
            "total_tokens": self.total_tokens,
            "cap": self.cap,
            "remaining": max(0, self.cap - self.total_tokens),
        }
