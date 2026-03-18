"""Rebuild-track helpers for ontology-first domain packages."""

from .loader import discover_v2_package_roots, load_domain_package_v2
from .models import DomainPackageV2, OntologyClass, OntologyClassesDocument, PackageMetadata
from .projection import (
    build_ontology_alias_rows,
    build_ontology_class_rows,
    build_ontology_mapping_rows,
    make_ontology_class_key,
)

__all__ = [
    "DomainPackageV2",
    "OntologyClass",
    "OntologyClassesDocument",
    "PackageMetadata",
    "discover_v2_package_roots",
    "load_domain_package_v2",
    "build_ontology_alias_rows",
    "build_ontology_class_rows",
    "build_ontology_mapping_rows",
    "make_ontology_class_key",
]
