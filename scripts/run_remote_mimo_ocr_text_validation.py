#!/usr/bin/env python3
"""Two-stage validation: remote MiMo OCR -> local text extraction."""

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
import run_remote_mimo_ocr_validation as mimo


DEFAULT_OCR_MODEL = "mimo-v2.5"
DEFAULT_TEXT_MODEL = "gemma-4-e4b-it-4bit"


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


def call_text_model(
    api_base: str,
    api_key: str,
    model: str,
    ocr_text: str,
) -> tuple[dict[str, Any], str]:
    system_prompt, user_prompt = text_prompt(ocr_text)
    payload = {
        "model": model,
        "temperature": 0.0,
        "max_tokens": 512,
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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mimo-run-dir", type=Path, required=True)
    parser.add_argument("--text-api-base", default="http://127.0.0.1:7999/v1")
    parser.add_argument("--text-api-key", default=os.getenv("OMLX_API_KEY", "4496"))
    parser.add_argument("--text-model", default=DEFAULT_TEXT_MODEL)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=mm.ROOT / "output" / "multimodal_validation",
    )
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    return parser.parse_args(argv)


def extract_ocr_rows(run_dir: Path) -> list[dict[str, Any]]:
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    return [row for row in summary.get("results", []) if row.get("status") == "ok"]


def write_report(
    output_dir: Path,
    run_id: str,
    mimo_run_dir: Path,
    text_model: str,
    results: list[dict[str, Any]],
) -> None:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in results:
        grouped[int(row["page"])].append(row)

    lines = [
        "# Remote MiMo OCR -> Local Text Validation Report",
        "",
        f"**Run ID:** {run_id}",
        f"**MiMo OCR source:** {mimo_run_dir}",
        f"**OCR model:** {DEFAULT_OCR_MODEL}",
        f"**Text model:** {text_model}",
        "",
        "## Results",
        "",
    ]
    for page in sorted(grouped):
        row = grouped[page][0]
        if row["status"] == "ok":
            sample = "; ".join(row["parsed_lines"][:8]) or "none"
            matches = ", ".join(row["matched_expectations"]) or "none"
            lines.append(
                f"- Page {page}: parsed={len(row['parsed_lines'])}, matched_expected={matches}, sample={sample}"
            )
        else:
            lines.append(f"- Page {page}: failed, error={row['error_message']}")
    lines.extend(
        [
            "",
            "## Findings",
            "",
            "- This run isolates whether MiMo OCR text is good enough for a second-stage local parameter extractor.",
            "- Compare this report against the local GLM-OCR -> gemma run and the DeepSeek doc-level baseline.",
            "",
        ]
    )
    (output_dir / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.text_api_key:
        print("Missing local text API key.", file=os.sys.stderr)
        return 2
    if not args.mimo_run_dir.exists():
        print(f"run dir not found: {args.mimo_run_dir}", file=os.sys.stderr)
        return 2

    available_models = mm.load_models(args.text_api_base, args.text_api_key)
    if args.text_model not in available_models:
        print(f"missing local text model: {args.text_model}", file=os.sys.stderr)
        return 2

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_trane_remote_mimo_ocr_text_validation"
    output_dir = args.output_dir / run_id
    text_dir = output_dir / "text_responses"
    text_dir.mkdir(parents=True, exist_ok=False)

    results: list[dict[str, Any]] = []
    for ocr_row in extract_ocr_rows(args.mimo_run_dir):
        page = int(ocr_row["page"])
        start = time.monotonic()
        try:
            body, text = call_text_model(
                args.text_api_base,
                args.text_api_key,
                args.text_model,
                str(ocr_row.get("text") or ""),
            )
            parsed_lines = mm.parse_parameter_lines(text)
            result = {
                "model": args.text_model,
                "page": page,
                "status": "ok",
                "elapsed_seconds": time.monotonic() - start,
                "usage": body.get("usage", {}),
                "text": text,
                "parsed_lines": parsed_lines,
                "matched_expectations": mm.expectation_matches_in_text(
                    text,
                    mimo.DEFAULT_EXPECTATIONS.get(page, []),
                ),
                "error_message": None,
            }
            mm.write_json(
                text_dir / f"{mm.slugify(args.text_model)}_page_{page}.json",
                {
                    "request_page": page,
                    "model": args.text_model,
                    "response": body,
                    "text": text,
                    "parsed_lines": parsed_lines,
                },
            )
        except Exception as exc:  # noqa: BLE001
            result = {
                "model": args.text_model,
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
                text_dir / f"{mm.slugify(args.text_model)}_page_{page}.json",
                {
                    "request_page": page,
                    "model": args.text_model,
                    "error": result["error_message"],
                },
            )
        results.append(result)
        time.sleep(args.sleep_seconds)

    mm.write_json(
        output_dir / "summary.json",
        {
            "run_id": run_id,
            "mimo_run_dir": str(args.mimo_run_dir),
            "ocr_model": DEFAULT_OCR_MODEL,
            "text_model": args.text_model,
            "results": results,
        },
    )
    write_report(output_dir, run_id, args.mimo_run_dir, args.text_model, results)
    print(str(output_dir / "REPORT.md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
