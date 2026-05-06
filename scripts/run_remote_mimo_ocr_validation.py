#!/usr/bin/env python3
"""Run a remote Xiaomi MiMo OCR/transcription validation on selected manual pages."""

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
from urllib import request


ROOT = Path(__file__).resolve().parent.parent
RENDER_SCRIPT = ROOT / "scripts" / "render_pdf_page.swift"
DEFAULT_MODELS = ["mimo-v2.5", "mimo-v2-omni"]
DEFAULT_PAGES = [25, 29, 41, 45]
DEFAULT_EXPECTATIONS = {
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


@dataclass
class OcrResult:
    model: str
    page: int
    status: str
    elapsed_seconds: float
    text: str
    usage: dict[str, Any]
    matched_expectations: list[str]
    error_message: str | None = None


def read_local_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def resolve_api_key(cli_value: str | None) -> str | None:
    if cli_value:
        return cli_value
    env_value = os.getenv("MIMO_API_KEY")
    if env_value:
        return env_value
    local_env = read_local_env(ROOT / ".env.mimo.local")
    return local_env.get("MIMO_API_KEY")


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


def image_as_data_url(path: Path) -> str:
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{payload}"


def load_models(api_base: str, api_key: str) -> list[str]:
    req = request.Request(
        f"{api_base.rstrip('/')}/models",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    with request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return [item["id"] for item in payload.get("data", [])]


def build_messages() -> list[dict[str, Any]]:
    system = (
        "You are an OCR and transcription engine for HVAC equipment manuals. "
        "Transcribe visible text faithfully. Preserve parameter labels, units, ranges, "
        "table rows, English names, Chinese labels, and punctuation. Do not summarize."
    )
    user_text = (
        "Transcribe the visible text on this page. Focus especially on configurable setpoints, "
        "mode selections, limits, ranges, defaults, table rows, and field labels. "
        "Return plain text only. Do not explain."
    )
    return [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": "__IMAGE_URL__"}},
            ],
        },
    ]


def call_mimo_ocr(
    api_base: str,
    api_key: str,
    model: str,
    image_url: str,
    temperature: float,
    top_p: float,
    max_completion_tokens: int,
) -> tuple[dict[str, Any], str]:
    messages = build_messages()
    messages[1]["content"][1]["image_url"]["url"] = image_url
    payload = {
        "model": model,
        "messages": messages,
        "max_completion_tokens": max_completion_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "stream": False,
    }
    req = request.Request(
        f"{api_base.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=300) as response:
        body = json.loads(response.read().decode("utf-8"))
    content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    if isinstance(content, list):
        content = "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict)
        )
    return body, str(content).strip()


def expectation_matches(text: str, expectations: list[str]) -> list[str]:
    normalized = normalize_text(text)
    matched = []
    for item in expectations:
        if normalize_text(item) in normalized:
            matched.append(item)
    return matched


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def build_report(
    run_id: str,
    pdf_path: Path,
    models: list[str],
    pages: list[int],
    api_base: str,
    temperature: float,
    top_p: float,
    max_completion_tokens: int,
    results: list[OcrResult],
) -> str:
    grouped: dict[str, list[OcrResult]] = defaultdict(list)
    for result in results:
        grouped[result.model].append(result)

    lines = [
        "# Remote MiMo OCR Validation Report",
        "",
        f"**Run ID:** {run_id}",
        f"**PDF:** {pdf_path}",
        f"**API Base:** `{api_base}`",
        f"**Models:** {', '.join(models)}",
        f"**Pages:** {pages}",
        f"**Parameters:** temperature={temperature}, top_p={top_p}, max_completion_tokens={max_completion_tokens}",
        "",
        "## Results",
        "",
    ]
    for model in models:
        rows = grouped.get(model, [])
        lines.append(f"### {model}")
        lines.append("")
        for row in rows:
            if row.status == "ok":
                sample = row.text[:220].replace("\n", " ")
                matched = ", ".join(row.matched_expectations) or "none"
                lines.append(
                    f"- Page {row.page}: ok in {row.elapsed_seconds:.1f}s, matched_expected={matched}, sample={sample}"
                )
            else:
                lines.append(
                    f"- Page {row.page}: failed in {row.elapsed_seconds:.1f}s, error={row.error_message}"
                )
        lines.append("")

    lines.extend(
        [
            "## Notes",
            "",
            "- This run uses Xiaomi MiMo's OpenAI-compatible API with image input via `image_url`.",
            "- Outputs are raw OCR/transcription text intended for later parameter extraction comparison.",
            "- Page-level expectation hits are only a coarse proxy for OCR usefulness.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base", default="https://token-plan-sgp.xiaomimimo.com/v1")
    parser.add_argument("--api-key")
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--pages", default=",".join(str(page) for page in DEFAULT_PAGES))
    parser.add_argument("--models", default=",".join(DEFAULT_MODELS))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "output" / "multimodal_validation",
    )
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--max-completion-tokens", type=int, default=4096)
    parser.add_argument("--sleep-seconds", type=float, default=1.5)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    api_key = resolve_api_key(args.api_key)
    if not api_key or api_key == "__FILL_ME__":
        print(
            "Missing MIMO_API_KEY. Fill /Users/asteroida/work/KnowFabric-qwen-vl-validate/.env.mimo.local "
            "or pass --api-key.",
            file=sys.stderr,
        )
        return 2

    if not args.pdf.exists():
        print(f"pdf not found: {args.pdf}", file=sys.stderr)
        return 2

    pages = [int(part) for part in args.pages.split(",") if part.strip()]
    models = [part.strip() for part in args.models.split(",") if part.strip()]
    available_models = load_models(args.api_base, api_key)
    missing = [model for model in models if model not in available_models]
    if missing:
        print(f"missing remote models: {missing}", file=sys.stderr)
        print(f"available sample: {available_models[:20]}", file=sys.stderr)
        return 2

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_trane_remote_mimo_ocr"
    output_dir = args.output_dir / run_id
    pages_dir = output_dir / "pages"
    responses_dir = output_dir / "responses"
    pages_dir.mkdir(parents=True, exist_ok=False)
    responses_dir.mkdir(parents=True, exist_ok=False)

    for page in pages:
        render_page(args.pdf, page, pages_dir / f"page_{page}.png")

    results: list[OcrResult] = []
    for model in models:
        for page in pages:
            image_path = pages_dir / f"page_{page}.png"
            start = time.monotonic()
            try:
                response_body, text = call_mimo_ocr(
                    args.api_base,
                    api_key,
                    model,
                    image_as_data_url(image_path),
                    args.temperature,
                    args.top_p,
                    args.max_completion_tokens,
                )
                elapsed = time.monotonic() - start
                row = OcrResult(
                    model=model,
                    page=page,
                    status="ok",
                    elapsed_seconds=elapsed,
                    text=text,
                    usage=response_body.get("usage", {}),
                    matched_expectations=expectation_matches(
                        text,
                        DEFAULT_EXPECTATIONS.get(page, []),
                    ),
                )
                write_json(
                    responses_dir / f"{slugify(model)}_page_{page}.json",
                    {
                        "request_page": page,
                        "model": model,
                        "response": response_body,
                        "text": text,
                        "matched_expectations": row.matched_expectations,
                    },
                )
            except Exception as exc:  # noqa: BLE001
                elapsed = time.monotonic() - start
                row = OcrResult(
                    model=model,
                    page=page,
                    status="failed",
                    elapsed_seconds=elapsed,
                    text="",
                    usage={},
                    matched_expectations=[],
                    error_message=f"{type(exc).__name__}: {exc}",
                )
                write_json(
                    responses_dir / f"{slugify(model)}_page_{page}.json",
                    {
                        "request_page": page,
                        "model": model,
                        "error": row.error_message,
                    },
                )
            results.append(row)
            time.sleep(args.sleep_seconds)

    report = build_report(
        run_id,
        args.pdf,
        models,
        pages,
        args.api_base,
        args.temperature,
        args.top_p,
        args.max_completion_tokens,
        results,
    )
    (output_dir / "REPORT.md").write_text(report, encoding="utf-8")
    write_json(
        output_dir / "summary.json",
        {
            "run_id": run_id,
            "pdf": str(args.pdf),
            "api_base": args.api_base,
            "models": models,
            "pages": pages,
            "results": [row.__dict__ for row in results],
        },
    )
    print(str(output_dir / "REPORT.md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
