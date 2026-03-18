"""Tests for review scaffold generation from chunk backfill candidates."""

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
    OntologyClassV2,
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
from scripts.backfill_manual_knowledge_from_chunks import backfill_manual_fixture_from_chunks
from scripts.build_manual_fixture_from_review_candidates import build_manual_fixture_from_review_candidate_file
from scripts.build_review_scaffold_from_candidates import (
    build_review_scaffold_from_candidate_file,
    build_review_scaffold_from_candidates,
)
from scripts.generate_chunk_backfill_candidates import generate_chunk_backfill_candidates

REPO_ROOT = Path(__file__).resolve().parent.parent
HVAC_V2_ROOT = REPO_ROOT / "domain_packages/hvac/v2"
DRIVE_V2_ROOT = REPO_ROOT / "domain_packages/drive/v2"
HVAC_FIXTURE = REPO_ROOT / "tests/fixtures/manual_validation/hvac_module_faults.json"
DRIVE_PARAMETER_FIXTURE = REPO_ROOT / "tests/fixtures/manual_validation/drive_parameter_profiles.json"


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
            db.execute(OntologyClassV2.__table__.insert(), build_ontology_class_rows(bundle))
            db.execute(OntologyAliasV2.__table__.insert(), build_ontology_alias_rows(bundle))
            db.execute(OntologyMappingV2.__table__.insert(), build_ontology_mapping_rows(bundle))
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


def test_build_review_scaffold_from_candidates_prefills_review_blocks(monkeypatch) -> None:
    """Candidate payload should become a review-ready scaffold with curation defaults."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_fixture_chunks(session_factory, HVAC_FIXTURE)
    monkeypatch.setattr("scripts.generate_chunk_backfill_candidates.SessionLocal", session_factory)

    payload = generate_chunk_backfill_candidates(
        "hvac",
        doc_id="doc_aux_module_faults",
        equipment_class_id="air_cooled_modular_heat_pump",
    )
    scaffold = build_review_scaffold_from_candidates(payload, default_trust_level="L2")

    assert scaffold["review_mode"] == "chunk_backfill_review_scaffold"
    assert len(scaffold["candidate_entries"]) == 3
    first_entry = scaffold["candidate_entries"][0]
    assert first_entry["review_decision"] == "pending"
    assert first_entry["curation"]["canonical_key"] == first_entry["canonical_key_candidate"]
    assert first_entry["curation"]["structured_payload"] == first_entry["structured_payload_candidate"]
    assert first_entry["curation"]["trust_level"] == "L2"
    assert first_entry["curation"]["evidence_text"] == first_entry["evidence_text"]


def test_review_scaffold_file_can_round_trip_to_backfill(monkeypatch) -> None:
    """A minimally completed scaffold should feed the reviewed-fixture and backfill path."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_fixture_chunks(session_factory, DRIVE_PARAMETER_FIXTURE)
    monkeypatch.setattr("scripts.generate_chunk_backfill_candidates.SessionLocal", session_factory)
    monkeypatch.setattr("scripts.build_manual_fixture_from_review_candidates.SessionLocal", session_factory)
    monkeypatch.setattr("scripts.backfill_manual_knowledge_from_chunks.SessionLocal", session_factory)

    payload = generate_chunk_backfill_candidates(
        "drive",
        doc_id="doc_siemens_g120xa_manual",
        equipment_class_id="variable_frequency_drive",
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        candidate_path = Path(tmp_dir) / "candidates.json"
        scaffold_path = Path(tmp_dir) / "review_scaffold.json"
        fixture_path = Path(tmp_dir) / "reviewed_fixture.json"
        candidate_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        scaffold = build_review_scaffold_from_candidate_file(candidate_path, default_trust_level="L2")
        for entry in scaffold["candidate_entries"]:
            entry["review_decision"] = "accepted"
            entry["curation"]["title"] = f"Reviewed {entry['canonical_key_candidate']} parameter"
            entry["curation"]["summary"] = f"Reviewed semantic parameter candidate for {entry['canonical_key_candidate']}."
            entry["curation"]["applicability"] = {"brand": "Siemens", "model_family": "G120XA"}
        scaffold_path.write_text(json.dumps(scaffold, ensure_ascii=False, indent=2), encoding="utf-8")

        fixture = build_manual_fixture_from_review_candidate_file(scaffold_path)
        fixture_path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2), encoding="utf-8")
        equipment_class_key, knowledge_count = backfill_manual_fixture_from_chunks(fixture_path)

    db = session_factory()
    try:
        assert equipment_class_key == "drive:variable_frequency_drive"
        assert knowledge_count == 2
        assert db.query(KnowledgeObjectV2).filter(KnowledgeObjectV2.domain_id == "drive").count() == 2
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
    test_build_review_scaffold_from_candidates_prefills_review_blocks(monkeypatch)
    monkeypatch.undo()
    monkeypatch = _MonkeyPatch()
    test_review_scaffold_file_can_round_trip_to_backfill(monkeypatch)
    monkeypatch.undo()
    print("Review scaffold builder checks passed")
