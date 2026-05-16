#!/usr/bin/env python3
"""Inspect PDF page count and coarse text quality for source corpus collection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pypdf import PdfReader


def inspect_pdf(path: Path) -> dict[str, object]:
    reader = PdfReader(str(path))
    page_count = len(reader.pages)
    sampled_pages = min(page_count, 10)
    text_pages = 0
    chars = 0
    for page in reader.pages[:sampled_pages]:
        text = page.extract_text() or ""
        cleaned = "".join(text.split())
        chars += len(cleaned)
        if len(cleaned) >= 80:
            text_pages += 1
    quality = classify_quality(sampled_pages, text_pages, chars)
    return {
        "path": str(path),
        "page_count": page_count,
        "sampled_pages": sampled_pages,
        "sample_text_chars": chars,
        "text_quality": quality,
    }


def classify_quality(sampled_pages: int, text_pages: int, chars: int) -> str:
    if sampled_pages == 0:
        return "scanned"
    ratio = text_pages / sampled_pages
    if ratio >= 0.8 and chars >= sampled_pages * 120:
        return "text"
    if ratio >= 0.2:
        return "mixed"
    return "scanned"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf_path")
    args = parser.parse_args(argv)
    payload = inspect_pdf(Path(args.pdf_path))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
