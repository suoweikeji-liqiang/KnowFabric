#!/usr/bin/env python3
"""J1: Diagnose what names reach group_and_normalize in merge_with_existing.

Dumps output/diagnostic/<run_id>/apply_grouping_input.jsonl
with each line: {anchor, knowledge_type, names, n_names, has_trane, has_carrier, has_mcquay}
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.session import SessionLocal
from packages.db.models_v2 import KnowledgeObjectV2
from packages.compiler.cross_source_merger import merge_candidates
from packages.compiler.canonical_key import group_and_normalize
from sqlalchemy import text


def diagnose():
    session = SessionLocal()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(f"output/diagnostic/{run_id}")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "apply_grouping_input.jsonl"

    # Collect ALL existing centrifugal_chiller parameter_spec KOs
    kos = session.query(KnowledgeObjectV2).filter(
        KnowledgeObjectV2.ontology_class_id == 'centrifugal_chiller',
        KnowledgeObjectV2.knowledge_object_type == 'parameter_spec',
    ).all()

    print(f"Existing KOs: {len(kos)}")

    # Group by (anchor, type) — simulate what merge_with_existing does
    buckets: dict[tuple[str, str], list[KnowledgeObjectV2]] = defaultdict(list)
    for ko in kos:
        buckets[(ko.ontology_class_id, ko.knowledge_object_type)].append(ko)

    results = []
    for (anchor, ko_type), ko_list in sorted(buckets.items()):
        # Extract names as merge_candidates would
        names = []
        for ko in ko_list:
            payload = ko.structured_payload_json or {}
            name = payload.get("parameter_name") or ko.title or ko.canonical_key
            names.append(str(name).strip())

        unique_names = list(dict.fromkeys(names))

        # Check brand presence
        brands = set()
        for ko in ko_list:
            ev = session.execute(text(
                "SELECT d.publisher FROM knowledge_object_evidence koe "
                "JOIN document d ON d.doc_id = koe.doc_id "
                "WHERE koe.knowledge_object_id = :kid LIMIT 1"
            ), {"kid": ko.knowledge_object_id}).fetchone()
            if ev:
                pub = (ev[0] or "").lower()
                if "trane" in pub:
                    brands.add("trane")
                elif "开利" in pub or "carrier" in pub:
                    brands.add("carrier")
                elif "麦克" in pub or "mcquay" in pub:
                    brands.add("mcquay")

        entry = {
            "anchor": anchor,
            "knowledge_type": ko_type,
            "n_kos": len(ko_list),
            "n_unique_names": len(unique_names),
            "has_trane": "trane" in brands,
            "has_carrier": "carrier" in brands,
            "has_mcquay": "mcquay" in brands,
            "brands": sorted(brands),
            "names": unique_names[:30],  # first 30 for readability
        }
        results.append(entry)

        # Actually call group_and_normalize and check result
        if len(unique_names) >= 2:
            mapping = group_and_normalize(
                unique_names,
                domain_id="hvac",
                equipment_class_id=anchor,
                knowledge_object_type=ko_type,
                backend_name="mimo-v2-omni",
            )
            groups = defaultdict(list)
            for n, k in mapping.items():
                groups[k].append(n)
            multi = {k: v for k, v in groups.items() if len(v) >= 2}
            cross_groups = 0
            for k, members in multi.items():
                gbrands = set()
                for m in members:
                    for ko in ko_list:
                        pname = (ko.structured_payload_json or {}).get("parameter_name") or ko.title or ""
                        if pname == m:
                            ev2 = session.execute(text(
                                "SELECT d.publisher FROM knowledge_object_evidence koe "
                                "JOIN document d ON d.doc_id = koe.doc_id "
                                "WHERE koe.knowledge_object_id = :kid LIMIT 1"
                            ), {"kid": ko.knowledge_object_id}).fetchone()
                            if ev2:
                                gbrands.add(ev2[0] or "?")
                if len(gbrands) >= 2:
                    cross_groups += 1
            entry["llm_groups"] = len(groups)
            entry["llm_multi_name_groups"] = len(multi)
            entry["llm_cross_brand_groups"] = cross_groups

    with open(out_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Summary
    print(f"\nDiagnostic dump: {out_path}")
    for r in results:
        cross = r.get("llm_cross_brand_groups", "N/A")
        print(f"  {r['anchor']}/{r['knowledge_type']}: {r['n_kos']} KOs, {r['n_unique_names']} names, "
              f"brands={r['brands']}, groups={r.get('llm_groups','?')}, multi={r.get('llm_multi_name_groups','?')}, "
              f"cross_brand={cross}")

    session.close()
    return str(out_path)


def main() -> int:
    path = diagnose()
    print(f"\nDone. Output: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
