#!/usr/bin/env python3
"""Validate ontology-first domain packages for the rebuild track."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.domain_kit_v2.loader import discover_v2_package_roots, load_domain_package_v2


def main() -> int:
    base_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("domain_packages")
    package_roots = discover_v2_package_roots(base_dir)
    if not package_roots:
        print("No v2 domain packages found.")
        return 0
    for package_root in package_roots:
        bundle = load_domain_package_v2(package_root)
        class_count = len(bundle.ontology_classes.classes)
        print(f"Validated {bundle.package.domain_id} v2 package ({class_count} classes)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Domain package v2 validation failed: {exc}")
        raise SystemExit(1)
