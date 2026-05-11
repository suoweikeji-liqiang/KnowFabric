"""Identify high-value visual pages without calling LLM.

Uses cheap heuristics (chunk text length, chunk type, doc text_quality)
to avoid burning MiMo quota on pages that are pure text.
"""

from __future__ import annotations

from typing import Any

TEXT_CHAR_THRESHOLD = 200
VISUAL_CHUNK_TYPES = {"figure", "diagram", "table", "schematic", "wiring", "nameplate"}
LOW_TEXT_QUALITIES = {"low_or_no_text", "partial_text"}


def _is_visual_chunk(chunk: Any) -> bool:
    chunk_type = str(getattr(chunk, "chunk_type", "") or "").lower()
    if any(vct in chunk_type for vct in VISUAL_CHUNK_TYPES):
        return True
    text = str(getattr(chunk, "cleaned_text", "") or "")
    if len(text.strip()) < TEXT_CHAR_THRESHOLD:
        return True
    return False


def triage_pages(
    doc_id: str,
    pages: list[dict[str, Any]],
    *,
    text_quality: str | None = None,
) -> list[dict[str, Any]]:
    """Identify pages worth sending to MiMo visual extraction.

    Args:
        doc_id: Document ID.
        pages: List of page dicts with keys: page_no, page_id, chunks (list of chunk dicts).
        text_quality: Optional document-level text quality label.

    Returns:
        List of dicts with: page_no, page_id, suggested_image_type, reason.
    """
    force_all = text_quality in LOW_TEXT_QUALITIES
    candidates = []

    for page in pages:
        page_no = page.get("page_no") or page.get("page", 0)
        page_id = page.get("page_id", "")
        chunks = page.get("chunks") or []

        if force_all:
            candidates.append({
                "page_no": page_no,
                "page_id": page_id,
                "suggested_image_type": "other",
                "reason": f"doc text_quality={text_quality}, full-page candidate",
            })
            continue

        if not chunks:
            # No chunks at all → likely a visual-only page
            candidates.append({
                "page_no": page_no,
                "page_id": page_id,
                "suggested_image_type": "other",
                "reason": "no chunks on page, likely visual-only",
            })
            continue

        visual_chunks = [c for c in chunks if _is_visual_chunk(c)]
        if visual_chunks:
            chunk_types = {str(getattr(c, "chunk_type", "") or "") for c in visual_chunks}
            suggested_type = "other"
            for ct in chunk_types:
                ct_lower = ct.lower()
                if "wiring" in ct_lower or "diagram" in ct_lower:
                    suggested_type = "wiring_diagram"
                elif "table" in ct_lower:
                    suggested_type = "parameter_table"
                elif "nameplate" in ct_lower:
                    suggested_type = "nameplate"
                elif "schematic" in ct_lower:
                    suggested_type = "system_schematic"

            candidates.append({
                "page_no": page_no,
                "page_id": page_id,
                "suggested_image_type": suggested_type,
                "reason": f"{len(visual_chunks)}/{len(chunks)} chunks are visual",
            })

    return candidates
