#!/usr/bin/env python3
"""Run Xiaomi MiMo page-level visual-semantic validation for HVAC documents."""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import request

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.llm_backend_config import load_backend  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RENDER_SCRIPT = ROOT / "scripts" / "render_pdf_page.swift"
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


@dataclass
class PageResult:
    page: int
    status: str
    elapsed_seconds: float
    parsed: dict[str, Any] | None
    raw_text: str
    usage: dict[str, Any]
    error_message: str | None = None


def render_page(pdf_path: Path, page: int, output_png: Path) -> None:
    output_png.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["swift", str(RENDER_SCRIPT), str(pdf_path), str(page), str(output_png)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def image_as_data_url(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def build_messages(image_url: str) -> list[dict[str, Any]]:
    system = (
        "You inspect HVAC manual page images for visual evidence. This is not OCR-only. "
        "Classify the visible page/region and extract only clearly visible visual facts. "
        "For diagrams, focus on components, terminals, signals, connections, and spatial relationships. "
        "If a relationship is uncertain, put it in summary, not relationships. Reply with strict JSON only."
    )
    user = (
        "Analyze this HVAC manual page as a visual evidence anchor. Return JSON with keys: "
        "page_type, summary, visual_entities, visual_relationships, useful_for_knowledge_types, "
        "ocr_text_if_useful, uncertainty_notes, confidence. "
        f"page_type must be one of: {', '.join(DEFAULT_PAGE_TYPES)}. "
        "visual_entities should be short objects with type and label. visual_relationships should be short objects "
        "with from, relation, to only when the connection or relationship is visibly supported."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": [{"type": "text", "text": user}, {"type": "image_url", "image_url": {"url": image_url}}]},
    ]


def call_mimo(api_base: str, api_key: str, model: str, image_url: str, args: argparse.Namespace) -> tuple[dict[str, Any], str]:
    payload = {
        "model": model,
        "messages": build_messages(image_url),
        "temperature": args.temperature,
        "top_p": args.top_p,
        "max_completion_tokens": args.max_completion_tokens,
        "response_format": {"type": "json_object"},
        "stream": False,
    }
    req = request.Request(
        f"{api_base.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=args.timeout_seconds) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body, response_text(body)


def response_text(body: dict[str, Any]) -> str:
    content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    if isinstance(content, list):
        return "".join(str(part.get("text", "")) for part in content if isinstance(part, dict)).strip()
    return str(content).strip()


def parse_json_or_empty(text: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def run_page(args: argparse.Namespace, page: int, pages_dir: Path, responses_dir: Path, backend) -> PageResult:
    image_path = pages_dir / f"page_{page}.png"
    render_page(args.pdf, page, image_path)
    start = time.monotonic()
    try:
        body, text = call_mimo(backend.api_base_url, backend.api_key, backend.model, image_as_data_url(image_path), args)
        parsed = parse_json_or_empty(text)
        result = PageResult(page, "ok" if parsed else "ok_unparsed_json", round(time.monotonic() - start, 3), parsed, text, body.get("usage", {}))
        write_json(responses_dir / f"page_{page}.json", {"page": page, "response": body, "parsed": parsed, "raw_text": text})
        return result
    except Exception as exc:  # noqa: BLE001
        result = PageResult(page, "failed", round(time.monotonic() - start, 3), None, "", {}, f"{type(exc).__name__}: {exc}")
        write_json(responses_dir / f"page_{page}.json", {"page": page, "error": result.error_message})
        return result


def render_report(run_id: str, args: argparse.Namespace, results: list[PageResult]) -> str:
    lines = [
        "# MiMo Visual Semantic Validation Report",
        "",
        f"- Run ID: `{run_id}`",
        f"- PDF: `{args.pdf}`",
        f"- Backend: `{args.backend_name}`",
        f"- Pages: `{args.pages}`",
        "",
        "| Page | Status | Type | Confidence | Seconds | Summary |",
        "|---:|---|---|---:|---:|---|",
    ]
    for row in results:
        parsed = row.parsed or {}
        summary = str(parsed.get("summary") or row.error_message or row.raw_text[:120]).replace("\n", " ")[:180]
        lines.append(
            f"| {row.page} | {row.status} | {parsed.get('page_type', '-')} | "
            f"{parsed.get('confidence', '-')} | {row.elapsed_seconds:.1f} | {summary} |"
        )
    return "\n".join(lines) + "\n"


def parse_pages(value: str) -> list[int]:
    return [int(part.strip()) for part in value.split(",") if part.strip()]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--pages", required=True, help="Comma-separated 1-based page numbers")
    parser.add_argument("--backend-name", default="mimo-v2.5-pro")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "output" / "visual_semantic_validation")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--max-completion-tokens", type=int, default=4096)
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    backend, _ = load_backend(args.backend_name)
    if not backend.api_key:
        print(f"Missing API key for backend {args.backend_name}", file=sys.stderr)
        return 2
    if not args.pdf.exists():
        print(f"pdf not found: {args.pdf}", file=sys.stderr)
        return 2
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_mimo_visual_semantic"
    output_dir = args.output_dir / run_id
    pages_dir = output_dir / "pages"
    responses_dir = output_dir / "responses"
    pages_dir.mkdir(parents=True, exist_ok=False)
    responses_dir.mkdir(parents=True, exist_ok=False)
    results = []
    for page in parse_pages(args.pages):
        results.append(run_page(args, page, pages_dir, responses_dir, backend))
        time.sleep(args.sleep_seconds)
    (output_dir / "REPORT.md").write_text(render_report(run_id, args, results), encoding="utf-8")
    write_json(output_dir / "summary.json", {"run_id": run_id, "pdf": str(args.pdf), "results": [row.__dict__ for row in results]})
    print(output_dir / "REPORT.md")
    return 1 if any(row.status == "failed" for row in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
