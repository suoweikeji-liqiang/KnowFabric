from pathlib import Path

import yaml


FIXTURE_ONTOLOGY = Path(__file__).resolve().parent / "fixtures" / "sw_base_model_ontology.yaml"


def test_export_seed_uses_sw_base_model_yaml_shape(tmp_path: Path) -> None:
    from scripts.export_ontology_seed_for_sw_base_model import export_ontology_seed

    output_path = tmp_path / "ontology_seed.yaml"
    summary = export_ontology_seed(
        None,
        output_path,
        include_mapping_types={"brick_to_external_standard"},
        ontology_path=FIXTURE_ONTOLOGY,
    )

    data = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert summary["equipment_classes"] >= 1
    assert summary["point_classes"] == 1
    assert summary["relation_types"] == 1
    assert data["ontology_version"] == "0.2.0"
    assert data["equipment_classes"][0]["class"] == "Chiller"
    assert data["point_classes"][0]["tags"]["measurement"] == "temperature"
    assert data["relation_types"][0]["inverse"] == "isPartOf"
