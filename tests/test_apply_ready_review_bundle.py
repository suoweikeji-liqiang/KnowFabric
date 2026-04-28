"""Tests for applying only ready packs from a prepared review bundle."""

import json
import sys
import tempfile
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.models import ContentChunk, Document, DocumentPage
from packages.db.models_v2 import (
    ChunkOntologyAnchorV2,
    KnowledgeObjectEvidenceV2,
    KnowledgeObjectV2,
    OntologyAliasV2,
    OntologyMappingV2,
)
from packages.db.session import Base
from packages.domain_kit_v2.loader import load_domain_package_v2
from packages.domain_kit_v2.manual_fixture import build_manual_fixture_rows, load_manual_fixture
from packages.domain_kit_v2.projection import (
    build_ontology_alias_rows,
    build_ontology_class_rows,
    build_ontology_mapping_rows,
)
from scripts.apply_ready_review_bundle import apply_ready_review_bundle
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
            OntologyAliasV2.__table__,
            OntologyMappingV2.__table__,
            ChunkOntologyAnchorV2.__table__,
            KnowledgeObjectV2.__table__,
            KnowledgeObjectEvidenceV2.__table__,
        ],
    )
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _seed_ontology(session_factory) -> None:
    db = session_factory()
    try:
        for root in (HVAC_V2_ROOT, DRIVE_V2_ROOT):
            bundle = load_domain_package_v2(root)
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


def test_apply_ready_review_bundle_is_safe_when_no_pack_is_ready(monkeypatch) -> None:
    """Prepared bundles with no ready packs should produce an empty apply report."""

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
        result = apply_ready_review_bundle(tmp_dir, prepare_manifest_path=manifest["paths"]["prepare_manifest"])
        stats = json.loads(Path(result["paths"]["stats"]).read_text(encoding="utf-8"))

    assert result["ready_pack_count"] == 0
    assert result["summary"] == {"applied": 0, "failed": 0}
    assert stats["overall"]["apply_status_counts"]["applied"] == 0


def test_apply_ready_review_bundle_applies_ready_pack_and_refreshes_summary(monkeypatch) -> None:
    """Marking one bootstrapped pack ready should apply it and refresh bundle outputs."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_fixture_chunks(session_factory, HVAC_FIXTURE)
    monkeypatch.setattr("scripts.generate_chunk_backfill_candidates.SessionLocal", session_factory)
    monkeypatch.setattr("scripts.build_manual_fixture_from_review_candidates.SessionLocal", session_factory)
    monkeypatch.setattr("scripts.backfill_manual_knowledge_from_chunks.SessionLocal", session_factory)

    with tempfile.TemporaryDirectory() as tmp_dir:
        manifest = prepare_review_pipeline_bundle(
            "hvac",
            tmp_dir,
            equipment_class_id="air_cooled_modular_heat_pump",
            default_trust_level="L2",
        )
        bootstrapped_pack = Path(manifest["paths"]["bootstrapped_review_pack_dir"]) / (
            "hvac__doc_aux_module_faults__air_cooled_modular_heat_pump.json"
        )
        payload = json.loads(bootstrapped_pack.read_text(encoding="utf-8"))
        for entry in payload["candidate_entries"]:
            if entry["canonical_key_candidate"] == "E22":
                entry["review_decision"] = "accepted"
                entry["curation"]["applicability"] = {"brand": "AUX", "model_family": "X Module Unit"}
            else:
                entry["review_decision"] = "rejected"
        bootstrapped_pack.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        # Refresh readiness after the manual edit, then apply only ready packs.
        from scripts.check_review_pack_readiness import check_review_pack_directory

        check_review_pack_directory(manifest["paths"]["bootstrapped_review_pack_dir"])
        result = apply_ready_review_bundle(tmp_dir, prepare_manifest_path=manifest["paths"]["prepare_manifest"])
        stats = json.loads(Path(result["paths"]["stats"]).read_text(encoding="utf-8"))
        summary_text = Path(result["paths"]["summary_text"]).read_text(encoding="utf-8")
        assert Path(result["paths"]["apply_report"]).exists()

    db = session_factory()
    try:
        assert result["ready_pack_count"] == 1
        assert result["summary"] == {"applied": 1, "failed": 0}
        assert stats["overall"]["apply_status_counts"]["applied"] == 1
        assert stats["overall"]["readiness_status_counts"]["ready"] == 1
        assert "Apply: 1 applied" in summary_text
        assert db.query(KnowledgeObjectV2).filter(KnowledgeObjectV2.domain_id == "hvac").count() == 1
    finally:
        db.close()


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
    test_apply_ready_review_bundle_is_safe_when_no_pack_is_ready(monkeypatch)
    monkeypatch.undo()
    monkeypatch = _MonkeyPatch()
    test_apply_ready_review_bundle_applies_ready_pack_and_refreshes_summary(monkeypatch)
    monkeypatch.undo()
    print("Apply-ready review bundle checks passed")
