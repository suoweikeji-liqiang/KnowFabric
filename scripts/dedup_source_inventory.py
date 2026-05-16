#!/usr/bin/env python3
"""Generate a SHA-256 duplicate report for HVAC source inventory files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


SUPPORTED_SUFFIXES = {".pdf", ".docx", ".doc", ".xlsx"}


def latest_inventory_dir(root: Path) -> Path:
    candidates = sorted(path for path in root.iterdir() if path.is_dir()) if root.exists() else []
    if not candidates:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        target = root / run_id
        target.mkdir(parents=True, exist_ok=True)
        return target
    return candidates[-1]


def load_inventory_paths(inventory_csv: Path) -> list[Path]:
    if not inventory_csv.exists():
        return []
    with inventory_csv.open(encoding="utf-8", newline="") as handle:
        return [
            Path(row["path"])
            for row in csv.DictReader(handle)
            if row.get("path")
        ]


def collect_paths(inventory_csv: Path, extra_roots: list[Path]) -> list[Path]:
    paths = load_inventory_paths(inventory_csv)
    for root in extra_roots:
        if root.exists() and root.is_dir():
            paths.extend(path for path in root.rglob("*") if path.is_file())
        elif root.exists():
            paths.append(root)
    return sorted({path.resolve() for path in paths if path.suffix.lower() in SUPPORTED_SUFFIXES})


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_score(path: Path) -> tuple[int, int, int, str]:
    name = path.name
    ascii_snake = bool(re.fullmatch(r"[a-z0-9_.+\- ]+", name))
    has_duplicate_marker = bool(re.search(r"\(\d+\)| copy|副本", name, re.I))
    descriptive = bool(re.search(r"[a-z]+_[a-z0-9_]+", path.stem))
    return (
        1 if has_duplicate_marker else 0,
        0 if descriptive or ascii_snake else 1,
        len(str(path)),
        str(path).lower(),
    )


def duplicate_report(paths: list[Path]) -> list[dict[str, str]]:
    by_hash: dict[str, list[Path]] = defaultdict(list)
    for path in paths:
        if path.exists():
            by_hash[sha256_file(path)].append(path)
    rows = []
    for digest, members in sorted(by_hash.items()):
        if len(members) < 2:
            continue
        ordered = sorted(members, key=canonical_score)
        kept, dropped = ordered[0], ordered[1:]
        rows.append({
            "sha256": digest,
            "kept_path": str(kept),
            "dropped_paths": json.dumps([str(path) for path in dropped], ensure_ascii=False),
            "reason": "same sha256; kept lowest duplicate/canonical path score",
        })
    return rows


def write_report(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sha256", "kept_path", "dropped_paths", "reason"])
        writer.writeheader()
        writer.writerows(rows)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    default_inventory_dir = latest_inventory_dir(Path("workspace/hvac_source_inventory"))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", default=str(default_inventory_dir / "source_inventory.csv"))
    parser.add_argument("--output", default=str(default_inventory_dir / "dedup_report.csv"))
    parser.add_argument(
        "--extra-root",
        action="append",
        default=["storage/authority_sources"],
        help="Additional file or directory to scan; may be passed multiple times.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    paths = collect_paths(Path(args.inventory), [Path(value) for value in args.extra_root])
    rows = duplicate_report(paths)
    write_report(rows, Path(args.output))
    print(f"scanned={len(paths)} duplicate_groups={len(rows)} report={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
