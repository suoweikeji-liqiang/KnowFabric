"""Tests for end-to-end review pipeline artifact export."""

import json
import sys
import tempfile
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.models import ContentChunk, Document, DocumentPage
from packages.db.models_v2 import OntologyAliasV2, OntologyMappingV2
from packages.db.session import Base
from packages.domain_kit_v2.loader import load_domain_package_v2
from packages.domain_kit_v2.manual_fixture import build_manual_fixture_rows, load_manual_fixture
from packages.domain_kit_v2.projection import (
    build_ontology_alias_rows,
    build_ontology_class_rows,
    build_ontology_mapping_rows,
)
from scripts.export_review_pipeline_artifacts import export_review_pipeline_artifacts

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


def test_export_review_pipeline_artifacts_writes_full_bundle(monkeypatch) -> None:
    """Artifact export should write candidates, review packs, stats, and a manifest."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_fixture_chunks(session_factory, HVAC_FIXTURE)
    monkeypatch.setattr("scripts.generate_chunk_backfill_candidates.SessionLocal", session_factory)

    with tempfile.TemporaryDirectory() as tmp_dir:
        manifest = export_review_pipeline_artifacts(
            "hvac",
            tmp_dir,
            equipment_class_id="air_cooled_modular_heat_pump",
            default_trust_level="L2",
        )

        candidate_path = Path(manifest["paths"]["candidates"])
        review_pack_manifest_path = Path(manifest["paths"]["review_pack_manifest"])
        stats_path = Path(manifest["paths"]["stats"])
        artifact_manifest_path = Path(manifest["paths"]["artifact_manifest"])

        assert candidate_path.exists()
        assert review_pack_manifest_path.exists()
        assert stats_path.exists()
        assert artifact_manifest_path.exists()
        assert manifest["counts"] == {
            "candidate_entries": 5,
            "review_packs": 2,
            "documents": 2,
        }

        stats = json.loads(stats_path.read_text(encoding="utf-8"))
        assert stats["overall"]["candidate_entries"] == 5
        assert stats["overall"]["review_packs_total"] == 2


def test_export_review_pipeline_artifacts_respects_doc_filter(monkeypatch) -> None:
    """Doc-scoped export should emit only one review pack and one document summary."""

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
        stats = json.loads(Path(manifest["paths"]["stats"]).read_text(encoding="utf-8"))
        pack_manifest = json.loads(Path(manifest["paths"]["review_pack_manifest"]).read_text(encoding="utf-8"))

        assert manifest["counts"] == {
            "candidate_entries": 3,
            "review_packs": 1,
            "documents": 1,
        }
        assert stats["documents"] == [
            {
                "doc_id": "doc_aux_module_faults",
                "doc_name": "AUX Central AC Fault Codes (Modular and VRF).pdf",
                "scanned_chunks": 3,
                "matched_chunks": 3,
                "candidate_entries": 3,
                "candidate_hit_rate": 1.0,
                "review_decisions": {"accepted": 0, "rejected": 0, "pending": 3},
                "packs_total": 1,
                "packs_ready_to_apply": 0,
                "readiness_status_counts": {
                    "ready": 0,
                    "blocked_pending": 0,
                    "blocked_no_accepted": 0,
                    "blocked_invalid": 0,
                },
                "apply_status_counts": {
                    "applied": 0,
                    "skipped_pending": 0,
                    "skipped_no_accepted": 0,
                    "failed": 0,
                },
            }
        ]
        assert pack_manifest["total_packs"] == 1
        assert pack_manifest["packs"][0]["doc_id"] == "doc_aux_module_faults"


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
    test_export_review_pipeline_artifacts_writes_full_bundle(monkeypatch)
    monkeypatch.undo()
    monkeypatch = _MonkeyPatch()
    test_export_review_pipeline_artifacts_respects_doc_filter(monkeypatch)
    monkeypatch.undo()
    print("Review pipeline artifact export checks passed")
