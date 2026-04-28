"""Tests for syncing ontology package v2 metadata into storage tables."""

import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.models_v2 import OntologyAliasV2, OntologyClassV2, OntologyMappingV2
from packages.db.session import Base
from scripts.sync_ontology_package_v2 import sync_domain_package

REPO_ROOT = Path(__file__).resolve().parent.parent
HVAC_V2_ROOT = REPO_ROOT / "domain_packages/hvac/v2"


def _build_session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        engine,
        tables=[
            OntologyClassV2.__table__,
            OntologyAliasV2.__table__,
            OntologyMappingV2.__table__,
        ],
    )
    with engine.begin() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys=ON")
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def test_sync_domain_package_persists_classes_aliases_and_mappings(monkeypatch) -> None:
    """Sync should flush class rows before inserting aliases and mappings."""

    session_factory = _build_session_factory()
    monkeypatch.setattr("scripts.sync_ontology_package_v2.SessionLocal", session_factory)

    domain_id, class_count, alias_count, mapping_count = sync_domain_package(HVAC_V2_ROOT)

    db = session_factory()
    try:
        assert domain_id == "hvac"
        assert class_count > 0
        assert alias_count > 0
        assert mapping_count == 0
        assert db.query(OntologyClassV2).filter_by(domain_id="hvac").count() == class_count
        assert db.query(OntologyAliasV2).filter_by(domain_id="hvac").count() == alias_count
        assert db.query(OntologyMappingV2).filter_by(domain_id="hvac").count() == mapping_count
    finally:
        db.close()
