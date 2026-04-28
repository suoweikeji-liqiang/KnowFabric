"""Tests for terminal summary rendering of review pipeline stats."""

import json
import sys
import tempfile
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.models import ContentChunk, Document, DocumentPage
from packages.db.models_v2 import OntologyAliasV2, OntologyClassV2, OntologyMappingV2
from packages.db.session import Base
from packages.domain_kit_v2.loader import load_domain_package_v2
from packages.domain_kit_v2.manual_fixture import build_manual_fixture_rows, load_manual_fixture
from packages.domain_kit_v2.projection import (
    build_ontology_alias_rows,
    build_ontology_class_rows,
    build_ontology_mapping_rows,
)
from scripts.export_review_pipeline_artifacts import export_review_pipeline_artifacts
from scripts.print_review_pipeline_summary import (
    _load_stats_payload,
    build_review_pipeline_summary_text,
)
from scripts.summarize_review_pipeline_stats import summarize_review_pipeline_stats

REPO_ROOT = Path(__file__).resolve().parent.parent
HVAC_V2_ROOT = REPO_ROOT / "domain_packages/hvac/v2"
DRIVE_V2_ROOT = REPO_ROOT / "domain_packages/drive/v2"
HVAC_FIXTURE = REPO_ROOT / "tests/fixtures/manual_validation/hvac_module_faults.json"


def _build_session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        engine,
        tables=[
            Document.__table__,
            DocumentPage.__table__,
            ContentChunk.__table__,
            OntologyClassV2.__table__,
            OntologyAliasV2.__table__,
            OntologyMappingV2.__table__,
        ],
    )
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _seed_ontology(session_factory) -> None:
    db = session_factory()
    try:
        for root in (HVAC_V2_ROOT, DRIVE_V2_ROOT):
            bundle = load_domain_package_v2(root)
            db.execute(OntologyClassV2.__table__.insert(), build_ontology_class_rows(bundle))
            db.execute(OntologyAliasV2.__table__.insert(), build_ontology_alias_rows(bundle))
            mapping_rows = build_ontology_mapping_rows(bundle)
            if mapping_rows:
                db.execute(OntologyMappingV2.__table__.insert(), mapping_rows)
        db.commit()
    finally:
        db.close()


def _seed_fixture_chunks(session_factory, fixture_path: Path) -> None:
    fixture = load_manual_fixture(fixture_path)
    rows = build_manual_fixture_rows(fixture)
    db = session_factory()
    try:
        db.execute(Document.__table__.insert(), rows["documents"])
        db.execute(DocumentPage.__table__.insert(), rows["pages"])
        db.execute(ContentChunk.__table__.insert(), rows["chunks"])
        db.commit()
    finally:
        db.close()


def test_build_review_pipeline_summary_text_from_stats(monkeypatch) -> None:
    """Summary text should surface the key candidate and review counts."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_fixture_chunks(session_factory, HVAC_FIXTURE)
    monkeypatch.setattr("scripts.generate_chunk_backfill_candidates.SessionLocal", session_factory)

    stats = summarize_review_pipeline_stats(
        candidate_path=None,
        pack_dir=None,
        apply_report_path=None,
    )
    # Build a realistic stats payload by using exported candidates.
    with tempfile.TemporaryDirectory() as tmp_dir:
        manifest = export_review_pipeline_artifacts(
            "hvac",
            tmp_dir,
            equipment_class_id="air_cooled_modular_heat_pump",
        )
        stats = _load_stats_payload(manifest["paths"]["stats"])

    rendered = build_review_pipeline_summary_text(stats)
    assert "Review Pipeline Summary" in rendered
    assert "Candidates: 5 entries from 5/5 matched chunks (hit rate 1.000)" in rendered
    assert "Packs: 2 total, 0 ready, 2 pending, 0 rejected-only" in rendered
    assert "Readiness: 0 ready, 0 blocked-pending, 0 blocked-no-accepted, 0 blocked-invalid" in rendered
    assert "- doc_aux_module_faults: 3/3 matched chunks, 3 candidates" in rendered
    assert "Packs Needing Review" in rendered


def test_summary_loader_reads_exported_stats_file(monkeypatch) -> None:
    """Summary loader should read the exported stats artifact without mutation."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_fixture_chunks(session_factory, HVAC_FIXTURE)
    monkeypatch.setattr("scripts.generate_chunk_backfill_candidates.SessionLocal", session_factory)

    with tempfile.TemporaryDirectory() as tmp_dir:
        manifest = export_review_pipeline_artifacts(
            "hvac",
            tmp_dir,
            doc_id="doc_aux_module_faults",
            equipment_class_id="air_cooled_modular_heat_pump",
        )
        stats = _load_stats_payload(manifest["paths"]["stats"])

    assert stats["overall"]["candidate_entries"] == 3
    assert stats["overall"]["review_packs_total"] == 1
    assert stats["overall"]["readiness_status_counts"]["ready"] == 0
    assert stats["documents"][0]["doc_id"] == "doc_aux_module_faults"


if __name__ == "__main__":
    class _MonkeyPatch:
        def __init__(self) -> None:
            self._patches = []

        def setattr(self, target: str, value) -> None:
            module_name, attr_name = target.rsplit(".", 1)
            module = __import__(module_name, fromlist=[attr_name])
            original = getattr(module, attr_name)
            setattr(module, attr_name, value)
            self._patches.append((module, attr_name, original))

        def undo(self) -> None:
            while self._patches:
                module, attr_name, original = self._patches.pop()
                setattr(module, attr_name, original)

    monkeypatch = _MonkeyPatch()
    test_build_review_pipeline_summary_text_from_stats(monkeypatch)
    monkeypatch.undo()
    monkeypatch = _MonkeyPatch()
    test_summary_loader_reads_exported_stats_file(monkeypatch)
    monkeypatch.undo()
    print("Review pipeline summary checks passed")
