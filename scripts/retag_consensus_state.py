#!/usr/bin/env python3
"""Retag legacy material_conflict consensus states without reclustering."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.cross_source_merger import assert_valid_ko_identity, classify_conflicting_layers
from packages.core.semantic_contract_v2 import ConsensusState
from packages.db.session import SessionLocal


def _layers(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, str):
        payload = json.loads(payload)
    if not isinstance(payload, dict):
        return []
    layers = payload.get("layers") or []
    return [layer for layer in layers if isinstance(layer, dict)]


def _retag_state(row: dict[str, Any]) -> str:
    old_state = row.get("consensus_state")
    if old_state in {
        ConsensusState.AGREED.value,
        ConsensusState.PARTIAL_CONFLICT.value,
        ConsensusState.VALUE_DISAGREEMENT.value,
        ConsensusState.OVER_MERGE.value,
        ConsensusState.SINGLE_SOURCE.value,
    }:
        return str(old_state)

    if old_state != ConsensusState.MATERIAL_CONFLICT.value:
        return str(old_state or ConsensusState.UNDETERMINED.value)

    new_state = classify_conflicting_layers(_layers(row.get("authority_summary_json")))
    if new_state == ConsensusState.MATERIAL_CONFLICT.value:
        return ConsensusState.PARTIAL_CONFLICT.value
    return new_state


def _facet_summary(row: dict[str, Any]) -> str:
    layers = _layers(row.get("authority_summary_json"))
    return json.dumps(
        {
            "layers": [
                {
                    "publisher": layer.get("publisher"),
                    "source_name": layer.get("source_name"),
                    "value_summary": layer.get("value_summary"),
                }
                for layer in layers
            ]
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def retag_consensus_states(rows: list[dict[str, Any]], *, apply: bool = False) -> dict[str, Any]:
    """Return retag decisions for rows; DB writes are handled by main."""

    output_rows = []
    counts: Counter[str] = Counter()
    for row in rows:
        assert_valid_ko_identity(row, context=f"retag row {row.get('knowledge_object_id')}")
        old_state = str(row.get("consensus_state") or "")
        new_state = _retag_state(row)
        counts[new_state] += 1
        output_rows.append({
            **row,
            "old_state": old_state,
            "new_state": new_state,
            "changed": old_state != new_state,
            "facet_summary": _facet_summary(row),
        })
    return {"rows": output_rows, "counts": dict(counts), "apply": apply}


def _load_rows(session: Any) -> list[dict[str, Any]]:
    rows = session.execute(text(
        "SELECT knowledge_object_id, ontology_class_id, canonical_key, title, "
        "consensus_state, authority_summary_json "
        "FROM knowledge_object "
        "WHERE consensus_state IN ('material_conflict', 'value_disagreement', 'over_merge') "
        "ORDER BY knowledge_object_id"
    )).mappings().all()
    return [dict(row) for row in rows]


def _write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "knowledge_object_id",
                "ontology_class_id",
                "canonical_key",
                "title",
                "old_state",
                "new_state",
                "changed",
                "facet_summary",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in writer.fieldnames})


def _apply_updates(session: Any, rows: list[dict[str, Any]]) -> int:
    changed = [row for row in rows if row.get("changed")]
    for row in changed:
        session.execute(
            text(
                "UPDATE knowledge_object "
                "SET consensus_state = :state "
                "WHERE knowledge_object_id = :ko_id"
            ),
            {"state": row["new_state"], "ko_id": row["knowledge_object_id"]},
        )
    return len(changed)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="retag_report.csv path")
    parser.add_argument("--dry-run", action="store_true", help="Do not update DB")
    args = parser.parse_args(argv)

    session = SessionLocal()
    try:
        decisions = retag_consensus_states(_load_rows(session), apply=not args.dry_run)
        if not args.dry_run:
            updated = _apply_updates(session, decisions["rows"])
            session.commit()
        else:
            updated = 0
        _write_report(Path(args.output), decisions["rows"])
        print(json.dumps({
            "updated": updated,
            "counts": decisions["counts"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "output": args.output,
        }, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
