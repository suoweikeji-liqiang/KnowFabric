#!/usr/bin/env python3
"""Sync ontology-first domain package aliases and mappings into metadata tables."""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import delete

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.models_v2 import OntologyAliasV2, OntologyMappingV2
from packages.db.session import SessionLocal
from packages.domain_kit_v2.loader import discover_v2_package_roots, load_domain_package_v2
from packages.domain_kit_v2.projection import (
    build_ontology_alias_rows,
    build_ontology_class_rows,
    build_ontology_mapping_rows,
)


def sync_domain_package(package_root: Path) -> tuple[str, int, int, int]:
    """Sync one v2 package into ontology metadata tables."""

    bundle = load_domain_package_v2(package_root)
    class_count = len(build_ontology_class_rows(bundle))
    alias_rows = build_ontology_alias_rows(bundle)
    mapping_rows = build_ontology_mapping_rows(bundle)

    session = SessionLocal()
    try:
        session.execute(delete(OntologyAliasV2).where(OntologyAliasV2.domain_id == bundle.package.domain_id))
        if alias_rows:
            session.execute(OntologyAliasV2.__table__.insert(), alias_rows)

        session.execute(delete(OntologyMappingV2).where(OntologyMappingV2.domain_id == bundle.package.domain_id))
        if mapping_rows:
            session.execute(OntologyMappingV2.__table__.insert(), mapping_rows)

        session.commit()
        return bundle.package.domain_id, class_count, len(alias_rows), len(mapping_rows)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def main() -> int:
    base_dir = Path("domain_packages")
    if len(sys.argv) > 1:
        package_roots = [base_dir / sys.argv[1] / "v2"]
    else:
        package_roots = discover_v2_package_roots(base_dir)

    if not package_roots:
        print("No v2 domain packages found.")
        return 0

    for package_root in package_roots:
        domain_id, class_count, alias_count, mapping_count = sync_domain_package(package_root)
        print(
            f"Synced {domain_id} "
            f"(classes_external={class_count}, aliases={alias_count}, mappings={mapping_count})"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Ontology package v2 sync failed: {exc}")
        raise SystemExit(1)
