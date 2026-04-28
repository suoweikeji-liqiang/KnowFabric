"""End-to-end HVAC application guidance bundle flow through apply-ready and API."""

import json
import sys
import tempfile
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from apps.api.main import app
from packages.db.models import ContentChunk, Document, DocumentPage
from packages.db.models_v2 import (
    ChunkOntologyAnchorV2,
    KnowledgeObjectEvidenceV2,
    KnowledgeObjectV2,
    OntologyAliasV2,
    OntologyClassV2,
    OntologyMappingV2,
)
from packages.db.session import Base, get_db
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
HVAC_APPLICATION_FIXTURE = REPO_ROOT / "tests/fixtures/manual_validation/hvac_application_guidance.json"


def _build_client() -> tuple[TestClient, sessionmaker]:
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
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), testing_session


def _seed_ontology(session_factory: sessionmaker) -> None:
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


def _seed_fixture_chunks(session_factory: sessionmaker, fixture_path: Path) -> None:
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


def test_apply_ready_review_bundle_supports_hvac_application_guidance_candidates() -> None:
    """Prepared HVAC authority-style guide bundle should apply reviewed guidance into the new semantic route."""

    client, session_factory = _build_client()
    original_session_locals = {}
    try:
        _seed_ontology(session_factory)
        _seed_fixture_chunks(session_factory, HVAC_APPLICATION_FIXTURE)

        for target in (
            "scripts.generate_chunk_backfill_candidates.SessionLocal",
            "scripts.build_manual_fixture_from_review_candidates.SessionLocal",
            "scripts.backfill_manual_knowledge_from_chunks.SessionLocal",
        ):
            module_name, attr_name = target.rsplit(".", 1)
            module = __import__(module_name, fromlist=[attr_name])
            original_session_locals[target] = getattr(module, attr_name)
            setattr(module, attr_name, session_factory)

        with tempfile.TemporaryDirectory() as tmp_dir:
            manifest = prepare_review_pipeline_bundle(
                "hvac",
                tmp_dir,
                doc_id="doc_ashrae_guideline_36",
                equipment_class_id="ahu",
                default_trust_level="L2",
            )
            bootstrapped_pack = Path(manifest["paths"]["bootstrapped_review_pack_dir"]) / (
                "hvac__doc_ashrae_guideline_36__ahu.json"
            )
            payload = json.loads(bootstrapped_pack.read_text(encoding="utf-8"))
            for entry in payload["candidate_entries"]:
                entry["review_decision"] = "accepted"
                entry["curation"]["title"] = "Reviewed AHU System Mode Hierarchy"
                entry["curation"]["summary"] = "Reviewed AHU application guidance from ASHRAE Guideline 36."
                entry["curation"]["applicability"] = {"brand": "ASHRAE", "model_family": "Guideline 36"}
            bootstrapped_pack.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

            from scripts.check_review_pack_readiness import check_review_pack_directory

            check_review_pack_directory(manifest["paths"]["bootstrapped_review_pack_dir"])
            result = apply_ready_review_bundle(tmp_dir, prepare_manifest_path=manifest["paths"]["prepare_manifest"])
            assert result["summary"] == {"applied": 1, "failed": 0}

        response = client.get(
            "/api/v2/domains/hvac/equipment-classes/ahu/application-guidance"
            "?brand=ASHRAE"
        )
        payload = response.json()

        assert response.status_code == 200
        assert len(payload["data"]["items"]) == 1
        assert payload["data"]["items"][0]["knowledge_object_type"] == "application_guidance"
    finally:
        for target, original in original_session_locals.items():
            module_name, attr_name = target.rsplit(".", 1)
            module = __import__(module_name, fromlist=[attr_name])
            setattr(module, attr_name, original)
        app.dependency_overrides.clear()


if __name__ == "__main__":
    test_apply_ready_review_bundle_supports_hvac_application_guidance_candidates()
    print("Apply-ready HVAC application guidance bundle checks passed")
