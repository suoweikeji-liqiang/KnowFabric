from pathlib import Path

import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from packages.db.models_v2 import OntologyAliasV2, OntologyClassV2, OntologyMappingV2
from packages.db.session import Base


def _session_factory():
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
    return sessionmaker(bind=engine)


def _class_row(
    key: str,
    class_id: str,
    kind: str,
    label: str,
    metadata,
) -> dict:
    return {
        "ontology_class_key": key,
        "domain_id": "hvac",
        "ontology_class_id": class_id,
        "package_version": "2.0.0-alpha",
        "ontology_version": "2.0.0-alpha",
        "parent_class_key": None,
        "class_kind": kind,
        "primary_label": label,
        "labels_json": {"en": label},
        "knowledge_anchors_json": metadata,
        "is_active": True,
    }


def _seed_rows() -> list[dict]:
    return [
        _class_row(
            "hvac:chiller",
            "chiller",
            "equipment",
            "Chiller",
            {
                "typical_points": ["Chilled_Water_Supply_Temperature_Sensor"],
                "typical_relations": [{"relation": "feeds", "target_class": "Pump"}],
            },
        ),
        _class_row(
            "hvac:chw_supply_temp_sensor",
            "chw_supply_temp_sensor",
            "point",
            "CHW Supply Temperature Sensor",
            {
                "tags": {
                    "medium": "chilled_water",
                    "direction": "supply",
                    "measurement": "temperature",
                    "point_type": "sensor",
                }
            },
        ),
        _class_row(
            "hvac:feeds",
            "feeds",
            "relation",
            "Feeds",
            {"inverse": "isFedBy", "description": "Fluid or energy feed relationship."},
        ),
        _class_row("hvac:fault_code", "fault_code", "concept", "Fault Code", []),
    ]


def _insert_seed_data(db) -> None:
    db.execute(OntologyClassV2.__table__.insert(), _seed_rows())
    db.execute(
        OntologyMappingV2.__table__.insert(),
        {
            "mapping_id": "map_chiller_brick",
            "ontology_class_key": "hvac:chiller",
            "domain_id": "hvac",
            "ontology_class_id": "chiller",
            "mapping_system": "brick",
            "external_id": "brick:Chiller",
            "mapping_metadata_json": {"source": "classes.yaml"},
            "is_primary": True,
        },
    )
    db.commit()


def test_export_seed_uses_sw_base_model_yaml_shape(tmp_path: Path) -> None:
    from scripts.export_ontology_seed_for_sw_base_model import export_ontology_seed

    session_factory = _session_factory()
    with session_factory() as db:
        _insert_seed_data(db)
        output_path = tmp_path / "ontology_seed.yaml"
        summary = export_ontology_seed(
            db,
            output_path,
            include_mapping_types={"brick_to_external_standard"},
        )

    data = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert summary == {"equipment_classes": 1, "point_classes": 1, "relation_types": 1}
    assert data["ontology_version"] == "0.1.0"
    assert data["equipment_classes"] == [
        {
            "class": "Chiller",
            "parent": None,
            "namespace": "brick",
            "typical_points": ["Chilled_Water_Supply_Temperature_Sensor"],
            "typical_relations": [{"relation": "feeds", "target_class": "Pump"}],
        }
    ]
    assert data["point_classes"][0]["tags"]["measurement"] == "temperature"
    assert data["relation_types"][0]["inverse"] == "isFedBy"
