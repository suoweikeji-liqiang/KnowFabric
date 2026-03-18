"""Tests for batch applying reviewed chunk backfill packs."""

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
from scripts.apply_review_packs_batch import apply_review_packs_in_directory
from scripts.build_review_packs_from_candidates import write_review_packs_from_candidate_file
from scripts.generate_chunk_backfill_candidates import generate_chunk_backfill_candidates

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


def _build_pack_dir(monkeypatch, session_factory, tmp_dir: str) -> Path:
    monkeypatch.setattr("scripts.generate_chunk_backfill_candidates.SessionLocal", session_factory)
    payload = generate_chunk_backfill_candidates(
        "hvac",
        equipment_class_id="air_cooled_modular_heat_pump",
    )
    candidate_path = Path(tmp_dir) / "candidates.json"
    candidate_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    pack_dir = Path(tmp_dir) / "review_packs"
    write_review_packs_from_candidate_file(candidate_path, pack_dir, default_trust_level="L2")
    return pack_dir


def _load_pack(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_pack(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_apply_review_packs_in_directory_applies_reviewed_and_skips_pending(monkeypatch) -> None:
    """Batch apply should backfill reviewed packs and skip unfinished ones."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_fixture_chunks(session_factory, HVAC_FIXTURE)
    monkeypatch.setattr("scripts.build_manual_fixture_from_review_candidates.SessionLocal", session_factory)
    monkeypatch.setattr("scripts.backfill_manual_knowledge_from_chunks.SessionLocal", session_factory)

    with tempfile.TemporaryDirectory() as tmp_dir:
        pack_dir = _build_pack_dir(monkeypatch, session_factory, tmp_dir)
        aux_pack = pack_dir / "hvac__doc_aux_module_faults__air_cooled_modular_heat_pump.json"
        guoxiang_pack = pack_dir / "hvac__doc_guoxiang_kms_manual__air_cooled_modular_heat_pump.json"

        aux_payload = _load_pack(aux_pack)
        for entry in aux_payload["candidate_entries"]:
            if entry["canonical_key_candidate"] == "E22":
                entry["review_decision"] = "accepted"
                entry["curation"]["title"] = "Reviewed AUX E22"
                entry["curation"]["summary"] = "Reviewed from batch pack."
                entry["curation"]["applicability"] = {"brand": "AUX", "model_family": "X Module Unit"}
            else:
                entry["review_decision"] = "rejected"
        _save_pack(aux_pack, aux_payload)

        report = apply_review_packs_in_directory(pack_dir)

        assert report["summary"] == {
            "applied": 1,
            "skipped_pending": 1,
            "skipped_no_accepted": 0,
            "failed": 0,
        }
        assert Path(report["report_path"]).exists()
        fixture_path = Path(report["results"][0]["fixture_path"])
        assert fixture_path.exists()
        assert guoxiang_pack.exists()

    db = session_factory()
    try:
        assert db.query(KnowledgeObjectV2).filter(KnowledgeObjectV2.domain_id == "hvac").count() == 1
    finally:
        db.close()


def test_apply_review_packs_in_directory_skips_rejected_only_pack(monkeypatch) -> None:
    """Packs with no accepted entries should be skipped without writing knowledge."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_fixture_chunks(session_factory, HVAC_FIXTURE)
    monkeypatch.setattr("scripts.build_manual_fixture_from_review_candidates.SessionLocal", session_factory)
    monkeypatch.setattr("scripts.backfill_manual_knowledge_from_chunks.SessionLocal", session_factory)

    with tempfile.TemporaryDirectory() as tmp_dir:
        pack_dir = _build_pack_dir(monkeypatch, session_factory, tmp_dir)
        aux_pack = pack_dir / "hvac__doc_aux_module_faults__air_cooled_modular_heat_pump.json"
        aux_payload = _load_pack(aux_pack)
        for entry in aux_payload["candidate_entries"]:
            entry["review_decision"] = "rejected"
        _save_pack(aux_pack, aux_payload)

        guoxiang_pack = pack_dir / "hvac__doc_guoxiang_kms_manual__air_cooled_modular_heat_pump.json"
        guoxiang_payload = _load_pack(guoxiang_pack)
        for entry in guoxiang_payload["candidate_entries"]:
            entry["review_decision"] = "rejected"
        _save_pack(guoxiang_pack, guoxiang_payload)

        report = apply_review_packs_in_directory(pack_dir)

        assert report["summary"] == {
            "applied": 0,
            "skipped_pending": 0,
            "skipped_no_accepted": 2,
            "failed": 0,
        }

    db = session_factory()
    try:
        assert db.query(KnowledgeObjectV2).count() == 0
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
    test_apply_review_packs_in_directory_applies_reviewed_and_skips_pending(monkeypatch)
    monkeypatch.undo()
    monkeypatch = _MonkeyPatch()
    test_apply_review_packs_in_directory_skips_rejected_only_pack(monkeypatch)
    monkeypatch.undo()
    print("Review pack batch apply checks passed")
