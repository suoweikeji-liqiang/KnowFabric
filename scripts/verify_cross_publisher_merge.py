#!/usr/bin/env python3
"""End-to-end ground-truth verification for cross-publisher KO merging.

Hand-written acceptance criterion. If THIS script passes, KnowFabric's
cross-publisher merger plumbing is verified working. If it fails, the
specific assertion that failed tells Codex exactly what to fix.

Usage:
    OMLX_API_KEY=4496 venv/bin/python scripts/verify_cross_publisher_merge.py
    OMLX_API_KEY=4496 venv/bin/python scripts/verify_cross_publisher_merge.py --keep
    # --keep: preserve test data in DB for manual inspection (default: cleanup)

Exit codes:
    0 — all assertions pass (cross-publisher merge fully working)
    1 — one or more assertions failed (see output for details)
    2 — environment / setup error (e.g. embedding API unreachable)

What it does:
  Step 1: Precheck BGE-M3 still returns expected sim for known same-concept pairs
  Step 2: Clean up any residue from previous test runs
  Step 3: Insert 6 test candidates spanning 3 publishers (Trane, Carrier, McQuay)
          using ontology_class_id='e2e_test_chiller' (isolated, no real data touched)
  Step 4: Invoke merge_with_existing as production apply path does
  Step 5: Assert:
          - total KO count ≤ 4 (real merging happened, not bulk insert)
          - ≥ 1 KO has authority_layers spanning ≥ 2 different publishers
          - "oil pressure" group merges Trane '油压差范围上限/下限' + Carrier '油压差'
          - "chilled water" group merges Trane '外部冷冻水设定范围上限'
            + McQuay '最低冷冻水出水温度'
  Step 6: Cleanup test data (unless --keep) so re-run is idempotent

This script does NOT touch real centrifugal_chiller data.

The 6 test candidates are derived from REAL DB parameter_names that the
operator observed are present right now in the chiller domain. Each pair is
verified at the embedding level to have cosine ≥ 0.80 (well above the 0.78
clustering threshold). If merge_with_existing fails to merge them, it is
because of a bug in apply path / canonical_key resolution / upsert logic,
NOT because of "extraction instability" or "naming complexity".
"""

from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("KNOWFABRIC_USE_EMBEDDING_FIRST", "1")

from packages.compiler.cross_source_merger import merge_with_existing  # noqa: E402
from packages.compiler.embedding_client import embed_one  # noqa: E402
from packages.db.models import ContentChunk, Document, DocumentPage  # noqa: E402
from packages.db.models_v2 import KnowledgeObjectEvidenceV2, KnowledgeObjectV2  # noqa: E402
from packages.db.session import SessionLocal  # noqa: E402

TEST_ANCHOR = "e2e_test_chiller"
TEST_TYPE = "parameter_spec"
BACKEND_NAME_DEFAULT = "deepseek-parameter-spec"

# Six candidates spanning 3 publishers. All names are real DB samples.
# Expected groupings (3 concept groups + 1 unrelated):
#   GROUP A "oil pressure": Trane 油压差范围上限/下限 + Carrier 油压差   → 3 layers cross-brand
#   GROUP B "chilled water": Trane 外部冷冻水设定 + McQuay 最低冷冻水    → 2 layers cross-brand
#   GROUP C "current limit": Trane 外部电流 + McQuay 电机负载范围下限   → 2 layers cross-brand (stretch)
#   GROUP D "anti-recycle": Carrier Anti-Recycle Time Delay              → 1 layer (no peer)
TEST_CANDIDATES: list[dict] = [
    {
        "name": "油压差范围上限",
        "publisher": "Trane",
        "doc_id": "test_doc_trane",
        "value": "100 psi",
        "evidence_text": "油压差范围上限设定值为 100 psi",
    },
    {
        "name": "油压差范围下限",
        "publisher": "Trane",
        "doc_id": "test_doc_trane",
        "value": "50 psi",
        "evidence_text": "油压差范围下限设定值为 50 psi",
    },
    {
        "name": "油压差",
        "publisher": "Carrier",
        "doc_id": "test_doc_carrier",
        "value": "75 psi",
        "evidence_text": "油压差 75 psi（典型工作点）",
    },
    {
        "name": "外部冷冻水设定范围上限",
        "publisher": "Trane",
        "doc_id": "test_doc_trane",
        "value": "50 °F",
        "evidence_text": "外部冷冻水设定范围上限 50 °F",
    },
    {
        "name": "最低冷冻水出水温度",
        "publisher": "McQuay",
        "doc_id": "test_doc_mcquay",
        "value": "4 °C",
        "evidence_text": "最低冷冻水出水温度 4 °C（含正确防冻液）",
    },
    {
        "name": "Anti-Recycle Time Delay",
        "publisher": "Carrier",
        "doc_id": "test_doc_carrier",
        "value": "5 minutes",
        "evidence_text": "Anti-Recycle Time Delay: 5 minutes",
    },
]

# Expected cross-brand merges. Each entry is a marker substring set;
# the group's parameter_name OR any evidence_text must contain ALL markers
# from the "all_of" list for the check to pass.
EXPECTED_CROSS_BRAND_GROUPS: list[dict] = [
    {
        "name": "oil pressure",
        "expected_publishers": {"Trane", "Carrier"},
        "marker_in_any_evidence": "油压差",
    },
    {
        "name": "chilled water",
        "expected_publishers": {"Trane", "McQuay"},
        "marker_in_any_evidence": "冷冻水",
    },
]


def _cos(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def precheck_embeddings() -> bool:
    """Step 1: Verify BGE-M3 still returns expected sim on known same-concept pairs."""
    print("=" * 70)
    print("Step 1: BGE-M3 embedding precheck")
    print("=" * 70)
    positive = [
        ("油压差范围上限", "油压差", 0.80),
        ("油压差范围下限", "油压差", 0.80),
        ("外部冷冻水设定范围上限", "最低冷冻水出水温度", 0.80),
    ]
    negative = [
        ("油压差", "Anti-Recycle Time Delay", 0.70),
    ]
    failed: list[tuple] = []
    for a, b, threshold in positive:
        try:
            ea, eb = embed_one(a), embed_one(b)
        except Exception as exc:
            print(f"  [ERROR] embedding failed for {a!r}/{b!r}: {exc}")
            return False
        sim = _cos(ea, eb)
        marker = "PASS" if sim >= threshold else "FAIL"
        print(f"  [{marker}] sim={sim:.3f}  {a!r}  ↔  {b!r}  (need ≥ {threshold})")
        if sim < threshold:
            failed.append((a, b, sim, threshold))
    for a, b, threshold in negative:
        try:
            ea, eb = embed_one(a), embed_one(b)
        except Exception as exc:
            print(f"  [ERROR] embedding failed for {a!r}/{b!r}: {exc}")
            return False
        sim = _cos(ea, eb)
        marker = "PASS" if sim < threshold else "FAIL"
        print(f"  [{marker}] sim={sim:.3f}  (NEG) {a!r}  ↔  {b!r}  (need < {threshold})")
        if sim >= threshold:
            failed.append((a, b, sim, threshold))
    if failed:
        print("\n  ✗ Embedding precheck FAILED. Fix BGE-M3 / oMLX / threshold before continuing.")
        for f in failed:
            print(f"    {f}")
        return False
    print("\n  ✓ Embedding precheck PASSED.\n")
    return True


TEST_DOC_IDS = {"test_doc_trane", "test_doc_carrier", "test_doc_mcquay"}


def _delete_test_data(session) -> tuple[int, int, int]:
    """Remove KOs, evidence, chunks, pages, documents created by this test.

    Returns (n_evidence, n_kos, n_fixtures).
    """
    ko_ids = [
        ko.knowledge_object_id
        for ko in session.query(KnowledgeObjectV2)
        .filter_by(ontology_class_id=TEST_ANCHOR)
        .all()
    ]
    n_ev = 0
    n_ko = 0
    if ko_ids:
        n_ev = (
            session.query(KnowledgeObjectEvidenceV2)
            .filter(KnowledgeObjectEvidenceV2.knowledge_object_id.in_(ko_ids))
            .delete(synchronize_session=False)
        )
        n_ko = (
            session.query(KnowledgeObjectV2)
            .filter_by(ontology_class_id=TEST_ANCHOR)
            .delete(synchronize_session=False)
        )
    n_chunks = (
        session.query(ContentChunk)
        .filter(ContentChunk.doc_id.in_(TEST_DOC_IDS))
        .delete(synchronize_session=False)
    )
    n_pages = (
        session.query(DocumentPage)
        .filter(DocumentPage.doc_id.in_(TEST_DOC_IDS))
        .delete(synchronize_session=False)
    )
    n_docs = (
        session.query(Document)
        .filter(Document.doc_id.in_(TEST_DOC_IDS))
        .delete(synchronize_session=False)
    )
    session.commit()
    return int(n_ev or 0), int(n_ko or 0), int((n_chunks or 0) + (n_pages or 0) + (n_docs or 0))


def setup_fixtures(session) -> dict[str, str]:
    """Pre-create Document / Page / Chunk rows so FK constraints are satisfied.

    Returns: {candidate_name: chunk_id} mapping
    """
    docs_info = {
        "test_doc_trane":   ("Trane",   "test_doc_trane_manual.pdf"),
        "test_doc_carrier": ("Carrier", "test_doc_carrier_manual.pdf"),
        "test_doc_mcquay":  ("McQuay",  "test_doc_mcquay_manual.pdf"),
    }
    # Create one Document + one Page per publisher
    for doc_id, (publisher, file_name) in docs_info.items():
        session.add(Document(
            doc_id=doc_id,
            file_hash=f"e2etest_{doc_id}",
            storage_path=f"/tmp/e2etest/{file_name}",
            file_name=file_name,
            file_ext=".pdf",
            mime_type="application/pdf",
            file_size=0,
            source_domain="hvac",
            authority_level="oem_manual",
            publisher=publisher,
            language="zh",
            is_redistributable=False,
        ))
        session.add(DocumentPage(
            page_id=f"test_page_{doc_id}",
            doc_id=doc_id,
            page_no=1,
            raw_text="(e2e test page)",
            cleaned_text="(e2e test page)",
        ))
    session.flush()
    # One chunk per candidate, all on the publisher's single page
    chunk_id_by_name = {}
    for i, c in enumerate(TEST_CANDIDATES):
        chunk_id = f"test_chunk_{hash(c['evidence_text']) & 0xFFFFFFFF:08x}"
        session.add(ContentChunk(
            chunk_id=chunk_id,
            doc_id=c["doc_id"],
            page_id=f"test_page_{c['doc_id']}",
            page_no=1,
            chunk_index=i,
            raw_text=c["evidence_text"],
            cleaned_text=c["evidence_text"],
            text_excerpt=c["evidence_text"][:200],
            chunk_type="parameter_table",
        ))
        chunk_id_by_name[c["name"]] = chunk_id
    session.commit()
    return chunk_id_by_name


def cleanup(session, label: str) -> None:
    n_ev, n_ko, n_fix = _delete_test_data(session)
    if n_ev or n_ko or n_fix:
        print(f"  [{label}] cleaned {n_ev} evidence + {n_ko} KOs + {n_fix} doc/page/chunk fixtures")
    else:
        print(f"  [{label}] no test data to clean")


def _build_candidate(c: dict, chunk_id_by_name: dict[str, str]) -> dict:
    chunk_id = chunk_id_by_name[c["name"]]
    return {
        "structured_payload": {
            "parameter_name": c["name"],
            "value": c["value"],
        },
        "title": c["name"],
        "summary": c["name"],
        "evidence_quote": c["evidence_text"],
        "evidence": [
            {
                "doc_id": c["doc_id"],
                "chunk_id": chunk_id,
                "page_id": f"test_page_{c['doc_id']}",
                "page_no": 1,
                "evidence_text": c["evidence_text"],
                "evidence_role": "primary",
            }
        ],
        "authority_level": "oem_manual",
        "publisher": c["publisher"],
        "citation": f"{c['doc_id']} p.1",
        "confidence_score": 0.9,
        "trust_level": "L3",
        "review_status": "published",
    }


def run_merger(session, backend_name: str, chunk_id_by_name: dict[str, str]) -> dict:
    print("=" * 70)
    print("Step 3-4: Run merge_with_existing on 6 test candidates")
    print("=" * 70)
    print(f"  Backend: {backend_name}")
    print(f"  Anchor: {TEST_ANCHOR} (isolated, does NOT touch real chiller data)")
    print(f"  Type:   {TEST_TYPE}")
    print(f"  Inputs ({len(TEST_CANDIDATES)}):")
    for c in TEST_CANDIDATES:
        print(f"    [{c['publisher']:7}] {c['name']}   ({c['value']})")
    print()

    candidates = [_build_candidate(c, chunk_id_by_name) for c in TEST_CANDIDATES]
    stats = merge_with_existing(
        session=session,
        new_candidates=candidates,
        domain_id="hvac",
        equipment_class_id=TEST_ANCHOR,
        ontology_class_key=f"hvac:{TEST_ANCHOR}",
        knowledge_object_type=TEST_TYPE,
        backend_name=backend_name,
    )
    session.commit()
    print(f"  merger stats: {stats}")
    print()
    return stats


def _collect_evidence_for_ko(session, ko_id: str) -> list[KnowledgeObjectEvidenceV2]:
    return (
        session.query(KnowledgeObjectEvidenceV2)
        .filter_by(knowledge_object_id=ko_id)
        .all()
    )


def verify(session) -> list[str]:
    print("=" * 70)
    print("Step 5: Verification (hard assertions)")
    print("=" * 70)
    kos = session.query(KnowledgeObjectV2).filter_by(ontology_class_id=TEST_ANCHOR).all()
    print(f"\n  Total KOs created: {len(kos)}")
    print(f"  Expected: ≤ 4 (3 concept groups + 1 unrelated)\n")

    by_pubs: list[tuple] = []
    for ko in kos:
        layers = (ko.authority_summary_json or {}).get("layers", [])
        pubs = sorted({l.get("publisher") for l in layers if l.get("publisher")})
        pname = (ko.structured_payload_json or {}).get("parameter_name") or ko.title or "???"
        marker = " ** CROSS-BRAND **" if len(pubs) >= 2 else ""
        print(
            f"  KO {ko.knowledge_object_id[:18]}  "
            f"layers={len(layers)} pubs={pubs} cons={ko.consensus_state}"
            f"{marker}"
        )
        print(f"      name=\"{pname[:60]}\"")
        evs = _collect_evidence_for_ko(session, ko.knowledge_object_id)
        for ev in evs[:3]:
            txt = (ev.evidence_text or "")[:80]
            print(f"      ev doc={ev.doc_id[:18]}  \"{txt}\"")
        by_pubs.append((ko, pubs, evs))
    print()

    failures: list[str] = []

    # Assertion 1: KO count ≤ 4
    if len(kos) > 4:
        failures.append(
            f"KO_COUNT_BLOAT: created {len(kos)} KOs, expected ≤ 4. "
            f"Likely cause: merger upsert reverse-lookup uses canonical_key (changes on regroup) "
            f"instead of parameter_name → INSERTs new KO instead of UPDATE existing."
        )
        print(f"  ✗ KO count {len(kos)} > 4")
    else:
        print(f"  ✓ KO count {len(kos)} ≤ 4")

    # Assertion 2: ≥ 1 cross-publisher KO
    cross_pubs = [(ko, pubs, evs) for ko, pubs, evs in by_pubs if len(pubs) >= 2]
    if not cross_pubs:
        failures.append(
            "NO_CROSS_PUB_KO: 0 KOs span ≥ 2 publishers. "
            "Likely cause: group_and_normalize input names did not include all publishers, "
            "OR LLM refinement split cross-brand cluster apart."
        )
        print(f"  ✗ cross-publisher KOs: 0")
    else:
        print(f"  ✓ cross-publisher KOs: {len(cross_pubs)}")

    # Assertion 3: oil pressure cross-brand merge
    # Trane '油压差范围上限/下限' + Carrier '油压差' should be one KO with both publishers
    oil_pressure_match = None
    for ko, pubs, evs in by_pubs:
        if "Trane" in pubs and "Carrier" in pubs:
            if any("油压差" in (ev.evidence_text or "") for ev in evs):
                oil_pressure_match = ko
                break
    if oil_pressure_match is None:
        failures.append(
            "OIL_PRESSURE_NOT_MERGED: Trane '油压差范围上限/下限' did not merge with Carrier '油压差'. "
            "Embedding sim is 0.94 (way above 0.78). If this fails, plumbing is broken or "
            "LLM refinement incorrectly split the cluster."
        )
        print("  ✗ Oil pressure: Trane '油压差范围上限/下限' + Carrier '油压差' NOT merged")
    else:
        print(f"  ✓ Oil pressure: cross-brand merged into {oil_pressure_match.canonical_key}")

    # Assertion 4: chilled water cross-brand merge
    chilled_water_match = None
    for ko, pubs, evs in by_pubs:
        if "Trane" in pubs and "McQuay" in pubs:
            if any("冷冻水" in (ev.evidence_text or "") for ev in evs):
                chilled_water_match = ko
                break
    if chilled_water_match is None:
        failures.append(
            "CHILLED_WATER_NOT_MERGED: Trane '外部冷冻水设定范围上限' did not merge with "
            "McQuay '最低冷冻水出水温度'. Embedding sim is 0.89 (above 0.78)."
        )
        print("  ✗ Chilled water: Trane '外部冷冻水设定范围上限' + McQuay '最低冷冻水出水温度' NOT merged")
    else:
        print(
            f"  ✓ Chilled water: cross-brand merged into {chilled_water_match.canonical_key}"
        )

    print()
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep test data in DB for manual inspection (default: cleanup at end)",
    )
    parser.add_argument(
        "--backend-name",
        default=BACKEND_NAME_DEFAULT,
        help=f"LLM backend for grouping refinement (default: {BACKEND_NAME_DEFAULT})",
    )
    parser.add_argument(
        "--skip-precheck",
        action="store_true",
        help="Skip BGE-M3 precheck (useful for offline test runs)",
    )
    args = parser.parse_args(argv)

    if not args.skip_precheck:
        if not precheck_embeddings():
            return 2

    db = SessionLocal()
    try:
        print("=" * 70)
        print("Step 2: Cleanup any residue from previous test runs")
        print("=" * 70)
        cleanup(db, "pre-run")
        print()

        print("=" * 70)
        print("Step 2b: Create test fixtures (doc / page / chunk for FK chain)")
        print("=" * 70)
        chunk_id_by_name = setup_fixtures(db)
        print(f"  Created 3 docs + 3 pages + {len(chunk_id_by_name)} chunks")
        print()

        run_merger(db, backend_name=args.backend_name, chunk_id_by_name=chunk_id_by_name)
        failures = verify(db)

        print("=" * 70)
        if failures:
            print(f"RESULT: FAIL ({len(failures)} assertion(s) failed)")
            print("=" * 70)
            for i, msg in enumerate(failures, 1):
                print(f"\n  [{i}] {msg}")
            print()
            return 1
        else:
            print("RESULT: PASS ✓ — Cross-publisher merge plumbing verified end-to-end.")
            print("=" * 70)
            return 0
    finally:
        if not args.keep:
            print()
            cleanup(db, "post-run")
        else:
            print()
            print("  [--keep] Test data preserved in DB (anchor=e2e_test_chiller). "
                  "Inspect with:\n    SELECT * FROM knowledge_object "
                  "WHERE ontology_class_id='e2e_test_chiller';")
        db.close()


if __name__ == "__main__":
    sys.exit(main())
