"""Filesystem loaders for ontology-first domain packages."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import DomainPackageV2, OntologyClassesDocument, PackageMetadata

PACKAGE_FILE = "package.yaml"
CLASSES_FILE = Path("ontology/classes.yaml")


def _load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing required file: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML object at the top level")
    return data


def load_domain_package_v2(package_root: str | Path) -> DomainPackageV2:
    """Load package metadata and ontology classes from a v2 package root."""

    root = Path(package_root).resolve()
    package_data = _load_yaml_file(root / PACKAGE_FILE)
    classes_data = _load_yaml_file(root / CLASSES_FILE)
    return DomainPackageV2(
        root_path=root,
        package=PackageMetadata.model_validate(package_data),
        ontology_classes=OntologyClassesDocument.model_validate(classes_data),
    )


def discover_v2_package_roots(base_dir: str | Path) -> list[Path]:
    """Discover domain package roots that expose a v2 package contract."""

    root = Path(base_dir).resolve()
    candidates = root.glob("*/v2")
    return sorted(path for path in candidates if path.is_dir() and (path / PACKAGE_FILE).exists())
