"""Tests for doc/equipment review pack building from candidates."""

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
from scripts.backfill_manual_knowledge_from_chunks import backfill_manual_fixture_from_chunks
from scripts.build_manual_fixture_from_review_candidates import build_manual_fixture_from_review_candidate_file
from scripts.build_review_packs_from_candidates import (
    build_review_packs_from_scaffold,
    write_review_packs_from_candidate_file,
)
from scripts.build_review_scaffold_from_candidates import build_review_scaffold_from_candidates
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


def _candidate_payload(monkeypatch, session_factory):
    monkeypatch.setattr("scripts.generate_chunk_backfill_candidates.SessionLocal", session_factory)
    return generate_chunk_backfill_candidates(
        "hvac",
        equipment_class_id="air_cooled_modular_heat_pump",
    )


def test_build_review_packs_from_scaffold_groups_by_doc_and_equipment(monkeypatch) -> None:
    """One scaffold should split into smaller review packs by doc/equipment."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_fixture_chunks(session_factory, HVAC_FIXTURE)

    scaffold = build_review_scaffold_from_candidates(_candidate_payload(monkeypatch, session_factory))
    packs = build_review_packs_from_scaffold(scaffold)

    assert len(packs) == 2
    summary = {
        (pack["doc_id"], pack["equipment_class"]["equipment_class_id"]): len(pack["candidate_entries"])
        for pack in packs
    }
    assert summary == {
        ("doc_aux_module_faults", "air_cooled_modular_heat_pump"): 3,
        ("doc_guoxiang_kms_manual", "air_cooled_modular_heat_pump"): 2,
    }


def test_write_review_packs_from_candidate_file_writes_manifest_and_files(monkeypatch) -> None:
    """Pack writer should emit one file per pack plus a manifest."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_fixture_chunks(session_factory, HVAC_FIXTURE)

    payload = _candidate_payload(monkeypatch, session_factory)
    with tempfile.TemporaryDirectory() as tmp_dir:
        candidate_path = Path(tmp_dir) / "candidates.json"
        output_dir = Path(tmp_dir) / "packs"
        candidate_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest = write_review_packs_from_candidate_file(candidate_path, output_dir, default_trust_level="L2")

        assert manifest["total_packs"] == 2
        pack_files = sorted(item["file_name"] for item in manifest["packs"])
        assert pack_files == [
            "hvac__doc_aux_module_faults__air_cooled_modular_heat_pump.json",
            "hvac__doc_guoxiang_kms_manual__air_cooled_modular_heat_pump.json",
        ]
        assert (output_dir / "review_pack_manifest.json").exists()
        assert (output_dir / pack_files[0]).exists()
        assert (output_dir / pack_files[1]).exists()


def test_review_pack_can_flow_into_existing_backfill(monkeypatch) -> None:
    """One accepted review pack should feed the reviewed-fixture and backfill path."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_fixture_chunks(session_factory, HVAC_FIXTURE)
    monkeypatch.setattr("scripts.generate_chunk_backfill_candidates.SessionLocal", session_factory)
    monkeypatch.setattr("scripts.build_manual_fixture_from_review_candidates.SessionLocal", session_factory)
    monkeypatch.setattr("scripts.backfill_manual_knowledge_from_chunks.SessionLocal", session_factory)

    payload = generate_chunk_backfill_candidates(
        "hvac",
        doc_id="doc_aux_module_faults",
        equipment_class_id="air_cooled_modular_heat_pump",
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        candidate_path = Path(tmp_dir) / "candidates.json"
        pack_dir = Path(tmp_dir) / "packs"
        candidate_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest = write_review_packs_from_candidate_file(candidate_path, pack_dir, default_trust_level="L2")

        pack_path = pack_dir / manifest["packs"][0]["file_name"]
        pack = json.loads(pack_path.read_text(encoding="utf-8"))
        accepted_key = "E22"
        for entry in pack["candidate_entries"]:
            if entry["canonical_key_candidate"] == accepted_key:
                entry["review_decision"] = "accepted"
                entry["curation"]["title"] = "Reviewed AUX E22 pack"
                entry["curation"]["summary"] = "Reviewed from pack workflow."
                entry["curation"]["applicability"] = {"brand": "AUX", "model_family": "X Module Unit"}
            else:
                entry["review_decision"] = "rejected"
        pack_path.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")

        fixture = build_manual_fixture_from_review_candidate_file(pack_path)
        fixture_path = Path(tmp_dir) / "reviewed_fixture.json"
        fixture_path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2), encoding="utf-8")
        equipment_class_key, knowledge_count = backfill_manual_fixture_from_chunks(fixture_path)

    db = session_factory()
    try:
        assert equipment_class_key == "hvac:air_cooled_modular_heat_pump"
        assert knowledge_count == 1
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
    test_build_review_packs_from_scaffold_groups_by_doc_and_equipment(monkeypatch)
    monkeypatch.undo()
    monkeypatch = _MonkeyPatch()
    test_write_review_packs_from_candidate_file_writes_manifest_and_files(monkeypatch)
    monkeypatch.undo()
    monkeypatch = _MonkeyPatch()
    test_review_pack_can_flow_into_existing_backfill(monkeypatch)
    monkeypatch.undo()
    print("Review pack builder checks passed")
