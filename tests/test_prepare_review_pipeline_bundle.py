"""Tests for one-shot review bundle preparation."""

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
from scripts.prepare_review_pipeline_bundle import prepare_review_pipeline_bundle

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


def test_prepare_review_pipeline_bundle_writes_full_prepared_bundle(monkeypatch) -> None:
    """Prepare command should export, bootstrap, check readiness, and render summary."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_fixture_chunks(session_factory, HVAC_FIXTURE)
    monkeypatch.setattr("scripts.generate_chunk_backfill_candidates.SessionLocal", session_factory)
    monkeypatch.setattr("scripts.build_manual_fixture_from_review_candidates.SessionLocal", session_factory)

    with tempfile.TemporaryDirectory() as tmp_dir:
        manifest = prepare_review_pipeline_bundle(
            "hvac",
            tmp_dir,
            equipment_class_id="air_cooled_modular_heat_pump",
            default_trust_level="L2",
        )

        assert Path(manifest["paths"]["prepare_manifest"]).exists()
        assert Path(manifest["paths"]["candidates"]).exists()
        assert Path(manifest["paths"]["review_pack_dir"]).exists()
        assert Path(manifest["paths"]["bootstrapped_review_pack_dir"]).exists()
        assert Path(manifest["paths"]["bootstrap_report"]).exists()
        assert Path(manifest["paths"]["readiness_report"]).exists()
        assert Path(manifest["paths"]["bootstrapped_stats"]).exists()
        assert Path(manifest["paths"]["health_report"]).exists()
        assert Path(manifest["paths"]["summary_text"]).exists()
        assert manifest["counts"] == {
            "candidate_entries": 5,
            "review_packs": 2,
            "bootstrapped_packs": 2,
            "ready_packs": 0,
        }
        assert manifest["health"]["total_findings"] >= 1

        summary_text = Path(manifest["paths"]["summary_text"]).read_text(encoding="utf-8")
        assert "Review Pipeline Summary" in summary_text
        assert "Packs: 2 total, 0 ready, 2 pending, 0 rejected-only" in summary_text
        assert "Readiness: 0 ready, 2 blocked-pending, 0 blocked-no-accepted, 0 blocked-invalid" in summary_text


def test_prepare_review_pipeline_bundle_respects_doc_filter(monkeypatch) -> None:
    """Doc-scoped prepare command should only emit one candidate pack and one doc summary."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_fixture_chunks(session_factory, HVAC_FIXTURE)
    monkeypatch.setattr("scripts.generate_chunk_backfill_candidates.SessionLocal", session_factory)
    monkeypatch.setattr("scripts.build_manual_fixture_from_review_candidates.SessionLocal", session_factory)

    with tempfile.TemporaryDirectory() as tmp_dir:
        manifest = prepare_review_pipeline_bundle(
            "hvac",
            tmp_dir,
            doc_id="doc_aux_module_faults",
            equipment_class_id="air_cooled_modular_heat_pump",
        )
        stats = json.loads(Path(manifest["paths"]["bootstrapped_stats"]).read_text(encoding="utf-8"))

    assert manifest["counts"] == {
        "candidate_entries": 3,
        "review_packs": 1,
        "bootstrapped_packs": 1,
        "ready_packs": 0,
    }
    assert len(stats["documents"]) == 1
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
    test_prepare_review_pipeline_bundle_writes_full_prepared_bundle(monkeypatch)
    monkeypatch.undo()
    monkeypatch = _MonkeyPatch()
    test_prepare_review_pipeline_bundle_respects_doc_filter(monkeypatch)
    monkeypatch.undo()
    print("Prepared review bundle checks passed")
