#!/usr/bin/env python3
"""Two-stage local validation: GLM-OCR page transcription -> local text extraction."""

from __future__ import annotations

import argparse
import json
import os
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import request

import run_local_multimodal_validation as mm


DEFAULT_PAGES = [25, 29, 41, 45]
DEFAULT_OCR_MODEL = "GLM-OCR-bf16"
DEFAULT_TEXT_MODELS = [
    "gemma-4-e4b-it-4bit",
    "Qwen3.5-4B-4bit",
    "Qwen3.5-9B-MLX-4bit",
]
PAGE_EXPECTATIONS = {
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
    ],
}


def text_prompt(ocr_text: str) -> tuple[str, str]:
    system = (
        "You extract configurable HVAC operational parameters from OCR text. "
        "Return terse plain text only."
    )
    user = (
        "From the OCR text below, extract only configurable operational parameters. "
        "Rules: exclude marketing claims, wiring/module features, non-configurable component labels, "
        "and generic UI navigation text. Keep one item per line in the format "
        "`parameter_name | exact evidence phrase`. The evidence phrase must be an exact substring of the OCR text. "
        "If there are no configurable parameters, output NONE.\n\n"
        f"OCR text:\n{ocr_text}"
    )
    return system, user


def call_text_model(api_base: str, api_key: str, model: str, ocr_text: str) -> tuple[dict[str, Any], str]:
    system_prompt, user_prompt = text_prompt(ocr_text)
    payload = {
        "model": model,
        "temperature": 0.0,
        "max_tokens": 320,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
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


def call_ocr_model(api_base: str, api_key: str, model: str, image_url: str) -> tuple[dict[str, Any], str]:
    payload = {
        "model": model,
        "temperature": 0.0,
        "max_tokens": 700,
        "messages": [
            {
                "role": "system",
                "content": "You are an OCR engine for HVAC manual pages. Transcribe visible text faithfully.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Transcribe this page with emphasis on setting tables, setpoints, ranges, defaults, "
                            "units, and mode options. Preserve English parameter names and Chinese labels. "
                            "Do not classify; just transcribe relevant text."
                        ),
                    },
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


def extract_ocr_text(run_dir: Path, page: int) -> str:
    path = run_dir / "ocr_responses" / f"{mm.slugify(DEFAULT_OCR_MODEL)}_page_{page}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return str(payload.get("text") or "")


def parse_lines(text: str) -> list[str]:
    return mm.parse_parameter_lines(text)


def matches(text: str, page: int) -> list[str]:
    return mm.expectation_matches_in_text(text, PAGE_EXPECTATIONS.get(page, []))


def write_report(
    output_dir: Path,
    run_id: str,
    pages: list[int],
    text_models: list[str],
    results: list[dict[str, Any]],
) -> None:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in results:
        grouped[row["model"]].append(row)

    lines = [
        "# Local OCR->Text Validation Report",
        "",
        f"**Run ID:** {run_id}",
        f"**OCR model:** {DEFAULT_OCR_MODEL}",
        f"**Text models:** {', '.join(text_models)}",
        f"**Pages:** {pages}",
        "",
        "## Results",
        "",
    ]
    for model in text_models:
        lines.append(f"### {model}")
        lines.append("")
        for row in grouped.get(model, []):
            if row["status"] == "ok":
                sample = "; ".join(row["parsed_lines"][:6]) or "none"
                lines.append(
                    f"- Page {row['page']}: parsed={len(row['parsed_lines'])}, matched_expected={', '.join(row['matched_expectations']) or 'none'}, sample={sample}"
                )
            else:
                lines.append(f"- Page {row['page']}: failed, error={row['error_message']}")
        lines.append("")

    lines.extend(
        [
            "## Findings",
            "",
            "- This run isolates whether local models fail because of image understanding or because of parameter classification/instruction following.",
            "- If a text model succeeds here but failed in the image-first run, the bottleneck was image-side control, not text extraction logic.",
            "",
        ]
    )
    (output_dir / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base", default="http://127.0.0.1:7999/v1")
    parser.add_argument("--api-key", default=os.getenv("OMLX_API_KEY"))
    parser.add_argument("--pdf", type=Path, default=mm.resolve_default_pdf())
    parser.add_argument("--pages", default=",".join(str(page) for page in DEFAULT_PAGES))
    parser.add_argument("--text-models", default=",".join(DEFAULT_TEXT_MODELS))
    parser.add_argument("--output-dir", type=Path, default=mm.ROOT / "output" / "multimodal_validation")
    parser.add_argument("--sleep-seconds", type=float, default=2.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.api_key:
        print("OMLX API key required via --api-key or OMLX_API_KEY", file=os.sys.stderr)
        return 2

    pages = [int(part) for part in args.pages.split(",") if part.strip()]
    text_models = [part.strip() for part in args.text_models.split(",") if part.strip()]
    available_models = mm.load_models(args.api_base, args.api_key)
    for model in [DEFAULT_OCR_MODEL, *text_models]:
        if model not in available_models:
            print(f"missing model: {model}", file=os.sys.stderr)
            return 2

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_trane_ocr_text_validation"
    output_dir = args.output_dir / run_id
    pages_dir = output_dir / "pages"
    ocr_dir = output_dir / "ocr_responses"
    text_dir = output_dir / "text_responses"
    pages_dir.mkdir(parents=True, exist_ok=False)
    ocr_dir.mkdir(parents=True, exist_ok=False)
    text_dir.mkdir(parents=True, exist_ok=False)

    for page in pages:
        page_png = pages_dir / f"page_{page}.png"
        mm.render_page(args.pdf, page, page_png)
        body, text = call_ocr_model(
            args.api_base,
            args.api_key,
            DEFAULT_OCR_MODEL,
            mm.read_image_as_data_url(page_png),
        )
        mm.write_json(
            ocr_dir / f"{mm.slugify(DEFAULT_OCR_MODEL)}_page_{page}.json",
            {"request_page": page, "model": DEFAULT_OCR_MODEL, "response": body, "text": text},
        )
        time.sleep(args.sleep_seconds)

    results: list[dict[str, Any]] = []
    for model in text_models:
        for page in pages:
            ocr_text = extract_ocr_text(output_dir, page)
            start = time.monotonic()
            try:
                body, text = call_text_model(args.api_base, args.api_key, model, ocr_text)
                parsed_lines = parse_lines(text)
                result = {
                    "model": model,
                    "page": page,
                    "status": "ok",
                    "elapsed_seconds": time.monotonic() - start,
                    "usage": body.get("usage", {}),
                    "text": text,
                    "parsed_lines": parsed_lines,
                    "matched_expectations": matches(text, page),
                    "error_message": None,
                }
                mm.write_json(
                    text_dir / f"{mm.slugify(model)}_page_{page}.json",
                    {"request_page": page, "model": model, "response": body, "text": text, "parsed_lines": parsed_lines},
                )
            except Exception as exc:  # noqa: BLE001
                result = {
                    "model": model,
                    "page": page,
                    "status": "failed",
                    "elapsed_seconds": time.monotonic() - start,
                    "usage": {},
                    "text": "",
                    "parsed_lines": [],
                    "matched_expectations": [],
                    "error_message": f"{type(exc).__name__}: {exc}",
                }
                mm.write_json(
                    text_dir / f"{mm.slugify(model)}_page_{page}.json",
                    {"request_page": page, "model": model, "error": result["error_message"]},
                )
            results.append(result)
            time.sleep(args.sleep_seconds)

    mm.write_json(
        output_dir / "summary.json",
        {
            "run_id": run_id,
            "pages": pages,
            "ocr_model": DEFAULT_OCR_MODEL,
            "text_models": text_models,
            "available_models": available_models,
            "results": results,
        },
    )
    write_report(output_dir, run_id, pages, text_models, results)
    print(str(output_dir / "REPORT.md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
