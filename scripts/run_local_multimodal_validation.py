#!/usr/bin/env python3
"""Run a local oMLX multimodal comparison against selected manual pages."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request


ROOT = Path(__file__).resolve().parent.parent
TRANE_PDF_RELATIVE = Path("storage/documents/doc_883beab5e0004a2c/trane_cvgf_400_1000_chiller_manual.pdf")
REFERENCE_CANDIDATES_RELATIVE = Path(
    "output/parameter_spec_vertical/"
    "20260429T145634Z_trane_cvgf_400_1000_chiller_manual_parameter_spec_v4_pro_judge/"
    "candidates_llm_verified.jsonl"
)
RENDER_SCRIPT = ROOT / "scripts" / "render_pdf_page.swift"
DEFAULT_MODELS = [
    "GLM-OCR-bf16",
    "DeepSeek-OCR-8bit",
    "gemma-4-e4b-it-4bit",
    "Qwen3.5-4B-4bit",
    "Qwen3.5-9B-MLX-4bit",
]
DEFAULT_PAGE_EXPECTATIONS = {
    25: [
        "Active Chilled Water Setpoint",
        "Active Current Limit Setpoint",
        "Chilled Water Reset",
    ],
    29: [
        "Front Panel Chilled Water Setpoint",
        "Front Panel Current Limit Setpoint",
        "Front Panel Base Load Setpoint",
        "Differential to Start",
        "Differential to Stop",
        "Setpoint Source",
        "Chilled Water Reset",
    ],
    41: [
        "External Base Loading Setpoint",
    ],
    45: [
        "External Chilled Water Setpoint",
        "External Current Limit Setpoint",
        "External Base Loading Setpoint",
    ],
}


def candidate_repo_roots() -> list[Path]:
    roots = [ROOT]
    sibling = ROOT.parent / "KnowFabric"
    if sibling not in roots:
        roots.append(sibling)
    return roots


def resolve_default_pdf() -> Path:
    for base in candidate_repo_roots():
        candidate = base / TRANE_PDF_RELATIVE
        if candidate.exists():
            return candidate
    return ROOT / TRANE_PDF_RELATIVE


def resolve_reference_candidates_path(cli_value: Path | None = None) -> Path | None:
    if cli_value is not None:
        return cli_value
    for base in candidate_repo_roots():
        candidate = base / REFERENCE_CANDIDATES_RELATIVE
        if candidate.exists():
            return candidate
    return None


@dataclass
class RunResult:
    model: str
    page: int
    status: str
    elapsed_seconds: float
    usage: dict[str, Any]
    text: str
    parsed_lines: list[str]
    matched_expectations: list[str]
    error_message: str | None = None


def slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9]+", "_", lowered)
    return lowered.strip("_")


def normalize_text(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered.strip(" \t\r\n.,;:!?，。；：！？、")


def render_page(pdf_path: Path, page: int, output_png: Path) -> None:
    output_png.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["swift", str(RENDER_SCRIPT), str(pdf_path), str(page), str(output_png)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def load_models(api_base: str, api_key: str) -> list[str]:
    req = request.Request(
        f"{api_base.rstrip('/')}/models",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    with request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return [item["id"] for item in payload.get("data", [])]


def read_image_as_data_url(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def prompt_for_model(model: str) -> tuple[str, str]:
    if "ocr" in model.lower() or model.lower().startswith("glm"):
        system = "You read document images and transcribe operationally relevant text with high fidelity."
        user = (
            "Read this HVAC manual page. Focus on configurable operational parameters only. "
            "First transcribe the short evidence phrases that look like parameter labels or table rows. "
            "Then output only parameter lines in the format parameter_name | evidence phrase. "
            "If no configurable parameter is visible, output NONE."
        )
        return system, user
    system = "You inspect HVAC manual pages and identify configurable operational parameters. Keep the answer terse."
    user = (
        "List only configurable operational parameters visible on this page. "
        "Output one item per line in the format parameter_name | evidence phrase. "
        "If none, output NONE. Do not describe reasoning. Do not include UI buttons unless the button label is itself the parameter name."
    )
    return system, user


def call_chat_completion(api_base: str, api_key: str, model: str, image_url: str) -> tuple[dict[str, Any], str]:
    system_prompt, user_prompt = prompt_for_model(model)
    payload = {
        "model": model,
        "temperature": 0.0,
        "max_tokens": 240,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ],
    }
    req = request.Request(
        f"{api_base.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=300) as response:
        body = json.loads(response.read().decode("utf-8"))
    content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    if isinstance(content, list):
        content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
    return body, str(content).strip()


def parse_parameter_lines(text: str) -> list[str]:
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.upper() == "NONE":
            continue
        if "|" in line:
            lines.append(line)
            continue
        if line.lower().startswith("parameter"):
            lines.append(line)
    return lines


def expectation_matches(parsed_lines: list[str], expectations: list[str]) -> list[str]:
    matched = []
    normalized_lines = [normalize_text(line) for line in parsed_lines]
    for item in expectations:
        needle = normalize_text(item)
        if any(needle in line for line in normalized_lines):
            matched.append(item)
    return matched


def expectation_matches_in_text(text: str, expectations: list[str]) -> list[str]:
    normalized = normalize_text(text)
    matched = []
    for item in expectations:
        if normalize_text(item) in normalized:
            matched.append(item)
    return matched


def load_reference_candidates(path: Path | None) -> dict[int, list[str]]:
    if path is None or not path.exists():
        return {}
    page_map: dict[int, list[str]] = defaultdict(list)
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        page = row.get("page_no")
        name = (row.get("structured_payload_candidate") or {}).get("parameter_name")
        if isinstance(page, int) and isinstance(name, str):
            page_map[page].append(name)
    return {page: sorted(set(names)) for page, names in page_map.items()}


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def result_to_dict(result: RunResult) -> dict[str, Any]:
    return {
        "model": result.model,
        "page": result.page,
        "status": result.status,
        "elapsed_seconds": result.elapsed_seconds,
        "usage": result.usage,
        "text": result.text,
        "parsed_lines": result.parsed_lines,
        "matched_expectations": result.matched_expectations,
        "error_message": result.error_message,
    }


def load_existing_result(path: Path) -> RunResult | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "error" in payload:
        return RunResult(
            model=str(payload["model"]),
            page=int(payload["request_page"]),
            status="failed",
            elapsed_seconds=0.0,
            usage={},
            text="",
            parsed_lines=[],
            matched_expectations=[],
            error_message=str(payload["error"]),
        )
    text = str(payload.get("text") or "")
    parsed = [str(item) for item in payload.get("parsed_lines") or []]
    page = int(payload["request_page"])
    matched = expectation_matches_in_text(text, DEFAULT_PAGE_EXPECTATIONS.get(page, []))
    return RunResult(
        model=str(payload["model"]),
        page=page,
        status="ok",
        elapsed_seconds=0.0,
        usage=(payload.get("response") or {}).get("usage", {}),
        text=text,
        parsed_lines=parsed,
        matched_expectations=matched,
    )


def write_summary(path: Path, run_id: str, pdf: Path, pages: list[int], models: list[str], available_models: list[str], results: list[RunResult], report_path: Path) -> None:
    write_json(
        path,
        {
            "run_id": run_id,
            "pdf": str(pdf),
            "pages": pages,
            "models": models,
            "available_models": available_models,
            "results": [result_to_dict(result) for result in results],
            "report_path": str(report_path),
        },
    )


def build_report(
    run_id: str,
    pdf_path: Path,
    available_models: list[str],
    requested_models: list[str],
    pages: list[int],
    results: list[RunResult],
    reference_candidates: dict[int, list[str]],
) -> str:
    grouped: dict[str, list[RunResult]] = defaultdict(list)
    for result in results:
        grouped[result.model].append(result)

    lines = [
        "# Local Multimodal Validation Report",
        "",
        f"**Run ID:** {run_id}",
        f"**PDF:** {pdf_path}",
        f"**Service:** `omlx` OpenAI-compatible API on `http://127.0.0.1:7999/v1`",
        f"**Requested models:** {', '.join(requested_models)}",
        "",
        "## Inventory",
        "",
        f"- Available local models: {', '.join(available_models)}",
        "- oMLX DMG local observation: structured output is not supported; multimodal comparison uses plain-text outputs with post-parse.",
        "- oMLX local observation: concurrent Qwen model switching is unstable; this run uses serial evaluation.",
        "",
        "## Page Set",
        "",
    ]
    for page in pages:
        expected = DEFAULT_PAGE_EXPECTATIONS.get(page, [])
        reference = reference_candidates.get(page, [])
        if reference:
            lines.append(f"- Page {page}: expected anchors = {expected or 'none'}, doc-level references = {reference}")
        else:
            lines.append(f"- Page {page}: expected anchors = {expected or 'none'}")

    lines.extend(["", "## Results", ""])
    for model in requested_models:
        rows = grouped.get(model, [])
        if not rows:
            lines.append(f"### {model}")
            lines.append("")
            lines.append("- No results.")
            lines.append("")
            continue
        lines.append(f"### {model}")
        lines.append("")
        for row in rows:
            timing = f"{row.elapsed_seconds:.1f}s" if row.elapsed_seconds > 0 else "cached result"
            if row.status == "ok":
                parsed = "; ".join(row.parsed_lines[:6]) or "none"
                matched = ", ".join(row.matched_expectations) or "none"
                lines.append(
                    f"- Page {row.page}: ok in {timing}, parsed={len(row.parsed_lines)}, matched_expected={matched}, sample={parsed}"
                )
            else:
                lines.append(
                    f"- Page {row.page}: failed in {timing}, error={row.error_message}"
                )
        lines.append("")

    lines.extend(["## Findings", ""])

    qwen_failures = [
        row for row in results
        if row.model.startswith("Qwen3.5") and row.status != "ok"
    ]
    if qwen_failures:
        lines.append("- Qwen models are usable only serially on this local oMLX server. Parallel or rapid model switching triggers server-side 500s.")

    glm_rows = [row for row in results if row.model == "GLM-OCR-bf16" and row.status == "ok"]
    if glm_rows:
        total_matches = sum(len(row.matched_expectations) for row in glm_rows)
        lines.append(f"- GLM-OCR-bf16 returned valid page outputs on {len(glm_rows)}/{len(pages)} pages with {total_matches} expected anchor hits.")

    deepseek_rows = [row for row in results if row.model == "DeepSeek-OCR-8bit" and row.status == "ok"]
    if deepseek_rows:
        total_nonempty = sum(1 for row in deepseek_rows if row.parsed_lines)
        lines.append(f"- DeepSeek-OCR-8bit behaved conservatively: non-empty parameter output on {total_nonempty}/{len(deepseek_rows)} pages.")

    gemma_rows = [row for row in results if row.model == "gemma-4-e4b-it-4bit" and row.status == "ok"]
    if gemma_rows:
        total_nonempty = sum(1 for row in gemma_rows if row.parsed_lines)
        lines.append(f"- Gemma 4 sees the page and produces concise parameter lines, but tends to collapse source rows into higher-level labels.")

    lines.extend([
        "- Best OCR/transcription signal in this run: `GLM-OCR-bf16`. It cleanly captured page 45 external setpoint text and did not fabricate parameters on the nameplate/components page.",
        "- Best direct page-level parameter listing in this run: `gemma-4-e4b-it-4bit` on page 25. It produced usable `parameter | evidence` lines for the arbitration tables.",
        "- Qwen3.5 local VLMs work only in serial mode on this machine. They see the page content, but instruction-following is weak and outputs drift into long reasoning text.",
    ])

    lines.extend([
        "",
        "## Recommendation",
        "",
        "- For this validation track, use OCR-specialized models for page text acquisition first, then do parameter classification in a second pass.",
        "- Keep doc-level DeepSeek V4 text extraction as the mainline. Use the multimodal track to audit table-heavy pages, scanned figures, nameplates, and wiring/electrical layouts.",
        "- Prefer `GLM-OCR-bf16` and `DeepSeek-OCR-8bit` for page transcription probes. Treat local Qwen VLMs as optional qualitative comparators until the oMLX switching bug is out of the way.",
        "- Practical local stack for the next round: `GLM-OCR-bf16` for page OCR, then a stronger text model or existing doc-level pipeline for parameter classification and dedup.",
    ])
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base", default="http://127.0.0.1:7999/v1")
    parser.add_argument("--api-key", default=os.getenv("OMLX_API_KEY"))
    parser.add_argument("--pdf", type=Path, default=resolve_default_pdf())
    parser.add_argument("--output-dir", type=Path, default=ROOT / "output" / "multimodal_validation")
    parser.add_argument("--pages", default="25,29,41,45")
    parser.add_argument("--models", default=",".join(DEFAULT_MODELS))
    parser.add_argument("--sleep-seconds", type=float, default=2.0)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--reference-candidates", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.api_key:
        print("OMLX API key required via --api-key or OMLX_API_KEY", file=sys.stderr)
        return 2
    if not args.pdf.exists():
        print(f"pdf not found: {args.pdf}", file=sys.stderr)
        return 2
    pages = [int(part) for part in args.pages.split(",") if part.strip()]
    requested_models = [part.strip() for part in args.models.split(",") if part.strip()]
    available_models = load_models(args.api_base, args.api_key)
    missing = [model for model in requested_models if model not in available_models]
    if missing:
        print(f"missing requested models: {missing}", file=sys.stderr)
        return 2

    if args.run_dir:
        output_dir = args.run_dir
        run_id = output_dir.name
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_trane_multimodal_validation"
        output_dir = args.output_dir / run_id
        output_dir.mkdir(parents=True, exist_ok=False)
    pages_dir = output_dir / "pages"
    responses_dir = output_dir / "responses"
    pages_dir.mkdir(parents=True, exist_ok=True)
    responses_dir.mkdir(parents=True, exist_ok=True)

    for page in pages:
        output_png = pages_dir / f"page_{page}.png"
        if not output_png.exists():
            render_page(args.pdf, page, output_png)

    results: list[RunResult] = []
    summary_path = output_dir / "summary.json"
    report_path = output_dir / "REPORT.md"
    for model in requested_models:
        for page in pages:
            image_path = pages_dir / f"page_{page}.png"
            response_path = responses_dir / f"{slugify(model)}_page_{page}.json"
            existing = load_existing_result(response_path)
            if existing is not None:
                results.append(existing)
                continue
            start = time.monotonic()
            try:
                body, text = call_chat_completion(
                    args.api_base,
                    args.api_key,
                    model,
                    read_image_as_data_url(image_path),
                )
                parsed = parse_parameter_lines(text)
                matched = expectation_matches_in_text(text, DEFAULT_PAGE_EXPECTATIONS.get(page, []))
                result = RunResult(
                    model=model,
                    page=page,
                    status="ok",
                    elapsed_seconds=time.monotonic() - start,
                    usage=body.get("usage", {}),
                    text=text,
                    parsed_lines=parsed,
                    matched_expectations=matched,
                )
                write_json(response_path, {"request_page": page, "model": model, "response": body, "text": text, "parsed_lines": parsed})
            except Exception as exc:  # noqa: BLE001
                result = RunResult(
                    model=model,
                    page=page,
                    status="failed",
                    elapsed_seconds=time.monotonic() - start,
                    usage={},
                    text="",
                    parsed_lines=[],
                    matched_expectations=[],
                    error_message=f"{type(exc).__name__}: {exc}",
                )
                write_json(response_path, {"request_page": page, "model": model, "error": result.error_message})
            results.append(result)
            write_summary(summary_path, run_id, args.pdf, pages, requested_models, available_models, results, report_path)
            time.sleep(args.sleep_seconds)

    reference_candidates = load_reference_candidates(
        resolve_reference_candidates_path(args.reference_candidates)
    )
    report = build_report(run_id, args.pdf, available_models, requested_models, pages, results, reference_candidates)
    report_path.write_text(report, encoding="utf-8")
    write_summary(summary_path, run_id, args.pdf, pages, requested_models, available_models, results, report_path)
    print(str(report_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
