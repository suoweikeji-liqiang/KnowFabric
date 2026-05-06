#!/usr/bin/env python3
"""Build a three-track comparison report for the Trane parameter extraction validation."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def normalize_name(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered.strip(" \t\r\n|.,;:!?，。；：！？、")


def parse_line_name(text: str) -> str:
    head = text.split("|", 1)[0]
    return normalize_name(head)


def load_deepseek(path: Path, pages: set[int]) -> dict[int, set[str]]:
    by_page: dict[int, set[str]] = defaultdict(set)
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        name = (row.get("structured_payload_candidate") or {}).get("parameter_name")
        if not isinstance(name, str):
            continue
        source_pages = row.get("source_page_nos") or []
        if not source_pages:
            page_no = row.get("page_no")
            if isinstance(page_no, int):
                source_pages = [page_no]
        for page in source_pages:
            if page in pages:
                by_page[int(page)].add(normalize_name(name))
    return by_page


def load_summary_lines(path: Path) -> dict[int, set[str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    by_page: dict[int, set[str]] = defaultdict(set)
    for row in payload.get("results", []):
        if row.get("status") != "ok":
            continue
        for line in row.get("parsed_lines") or []:
            by_page[int(row["page"])].add(parse_line_name(str(line)))
    return by_page


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deepseek-jsonl", type=Path, required=True)
    parser.add_argument("--local-summary", type=Path, required=True)
    parser.add_argument("--remote-summary", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--pages", default="25,29,41,45")
    args = parser.parse_args(argv)

    pages = {int(part) for part in args.pages.split(",") if part.strip()}
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_trane_multitrack_comparison"
    out_dir = args.output_dir / run_id
    out_dir.mkdir(parents=True, exist_ok=False)

    deepseek = load_deepseek(args.deepseek_jsonl, pages)
    local = load_summary_lines(args.local_summary)
    remote = load_summary_lines(args.remote_summary)

    lines = [
        "# Trane Parameter Extraction Three-Track Comparison",
        "",
        f"**Run ID:** {run_id}",
        f"**DeepSeek doc-level:** {args.deepseek_jsonl}",
        f"**Local GLM-OCR -> gemma:** {args.local_summary}",
        f"**Remote MiMo OCR -> gemma:** {args.remote_summary}",
        "",
        "## Per-page comparison",
        "",
    ]

    for page in sorted(pages):
        ds = deepseek.get(page, set())
        lc = local.get(page, set())
        rm = remote.get(page, set())
        three_way = ds & lc & rm
        lines.extend(
            [
                f"### Page {page}",
                "",
                f"- DeepSeek doc-level: {len(ds)}",
                f"- Local GLM-OCR -> gemma: {len(lc)}",
                f"- Remote MiMo OCR -> gemma: {len(rm)}",
                f"- Three-way overlap: {len(three_way)}",
                "",
                f"**DeepSeek only:** {', '.join(sorted(ds - lc - rm)) or 'none'}",
                "",
                f"**Local only:** {', '.join(sorted(lc - ds - rm)) or 'none'}",
                "",
                f"**Remote only:** {', '.join(sorted(rm - ds - lc)) or 'none'}",
                "",
                f"**Three-way overlap:** {', '.join(sorted(three_way)) or 'none'}",
                "",
            ]
        )

    union_ds = set().union(*deepseek.values()) if deepseek else set()
    union_local = set().union(*local.values()) if local else set()
    union_remote = set().union(*remote.values()) if remote else set()
    lines.extend(
        [
            "## Overall summary",
            "",
            f"- DeepSeek union: {len(union_ds)}",
            f"- Local GLM-OCR -> gemma union: {len(union_local)}",
            f"- Remote MiMo OCR -> gemma union: {len(union_remote)}",
            f"- DeepSeek ∩ Local: {len(union_ds & union_local)}",
            f"- DeepSeek ∩ Remote: {len(union_ds & union_remote)}",
            f"- Local ∩ Remote: {len(union_local & union_remote)}",
            "",
            "## Quick take",
            "",
            "- DeepSeek doc-level remains the highest-recall text-first baseline across the full manual.",
            "- Local GLM-OCR -> gemma reflects what the local image-first stack can recover on selected pages.",
            "- Remote MiMo OCR -> gemma tests whether a remote full-modal OCR source improves page-level parameter recovery.",
            "",
        ]
    )

    report_path = out_dir / "REPORT.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
