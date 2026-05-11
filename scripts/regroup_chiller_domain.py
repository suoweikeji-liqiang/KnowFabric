#!/usr/bin/env python3
"""M1: Re-group all chiller domain KOs through merge_with_existing (no new candidates)."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault('KNOWFABRIC_USE_EMBEDDING_FIRST', '1')

from packages.compiler.cross_source_merger import merge_with_existing
from packages.compiler.canonical_key import _save_registry, HASH_CACHE
from packages.db.session import SessionLocal


def main():
    _save_registry({"canonical_keys": {}})
    HASH_CACHE.clear()

    db = SessionLocal()
    stats = merge_with_existing(
        session=db,
        new_candidates=[],
        domain_id='hvac',
        equipment_class_id='centrifugal_chiller',
        ontology_class_key='hvac:centrifugal_chiller',
        knowledge_object_type='parameter_spec',
        backend_name='deepseek-parameter-spec',
    )
    print(f'stats: {stats}')
    db.commit()
    db.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
