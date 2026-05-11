#!/usr/bin/env python3
"""Task F: Rebuild canonical_key for all existing KOs via group_and_normalize.

One-shot job. Groups KOs by (ontology_class_id, knowledge_object_type),
runs LLM group_and_normalize per bucket, updates canonical_key in DB.

Governance exception (docs/36 §4.1): existing canonical_keys are mechanical
hash fallbacks, not authoritative. This rebuild is a one-time fix. After it
completes, canonical_key append-only rule resumes.
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.canonical_key import group_and_normalize, _save_registry, HASH_CACHE
from packages.db.models_v2 import KnowledgeObjectV2
from packages.db.session import SessionLocal


def rebuild(backend_name: str = "mimo-v2-omni", dry_run: bool = False) -> dict:
    _save_registry({"canonical_keys": {}})
    HASH_CACHE.clear()
    session = SessionLocal()

    kos = session.query(KnowledgeObjectV2).all()
    print(f"Total KOs: {len(kos)}")

    # Group by (ontology_class_id, knowledge_object_type)
    buckets: dict[tuple[str, str], list[KnowledgeObjectV2]] = defaultdict(list)
    for ko in kos:
        buckets[(ko.ontology_class_id, ko.knowledge_object_type)].append(ko)

    stats = {"buckets": len(buckets), "updated": 0, "unchanged": 0, "total_kos": len(kos)}
    print(f"Buckets: {len(buckets)}")

    for (anchor, ko_type), ko_list in sorted(buckets.items()):
        names = []
        for ko in ko_list:
            payload = ko.structured_payload_json or {}
            name = payload.get("parameter_name") or ko.title or ko.canonical_key
            names.append(str(name).strip())

        print(f"\n  {anchor}/{ko_type}: {len(ko_list)} KOs, {len(set(names))} unique names")

        if len(set(names)) <= 1:
            print(f"    Skip: only 1 unique name")
            continue

        try:
            mapping = group_and_normalize(
                names=names,
                domain_id="hvac",
                equipment_class_id=anchor,
                knowledge_object_type=ko_type,
                backend_name=backend_name,
            )
        except Exception as e:
            print(f"    LLM FAILED: {e}, skipping bucket")
            continue

        # Show groups
        grouped = defaultdict(list)
        for n, k in mapping.items():
            grouped[k].append(n)
        for k, members in sorted(grouped.items(), key=lambda x: -len(x[1])):
            if len(members) >= 2:
                print(f"    Group [{len(members)}] {k.split(':')[-1][:50]}:")
                for m in members:
                    print(f"      - {m[:60]}")

        # Update canonical_keys
        for ko, name in zip(ko_list, names):
            new_ck = mapping.get(name)
            if new_ck and new_ck != ko.canonical_key:
                if not dry_run:
                    ko.canonical_key = new_ck
                stats["updated"] += 1
                if stats["updated"] <= 20 or dry_run:
                    print(f"    UPDATE: {ko.canonical_key} → {new_ck}")
            else:
                stats["unchanged"] += 1

        if not dry_run:
            session.commit()

    session.close()
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--backend", default="mimo-v2-omni")
    args = parser.parse_args(argv)

    stats = rebuild(backend_name=args.backend, dry_run=args.dry_run)
    print(f"\n=== Summary ===")
    print(f"Buckets: {stats['buckets']}")
    print(f"Updated: {stats['updated']}")
    print(f"Unchanged: {stats['unchanged']}")
    print(f"Total KOs: {stats['total_kos']}")
    if args.dry_run:
        print("DRY RUN — no changes written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
