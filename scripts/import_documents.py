"""CLI script for document import."""
import sys
import argparse
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from packages.core.config import settings
from packages.core.logging import setup_logging
from packages.db.session import SessionLocal
from packages.storage.manager import StorageManager
from packages.ingest.service import IngestService
import logging

setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Import documents into KnowFabric')
    parser.add_argument('directory', help='Directory containing documents')
    parser.add_argument('--domain', help='Source domain (hvac, drive, etc.)')

    args = parser.parse_args()

    # Initialize services
    storage = StorageManager(settings.storage_root)
    ingest = IngestService(storage)
    db = SessionLocal()

    try:
        logger.info(f"Starting import from: {args.directory}")

        result = ingest.import_batch(
            db,
            args.directory,
            source_domain=args.domain
        )

        logger.info(
            f"Import complete",
            extra={
                'job_id': result['job_id'],
                'imported': result['imported'],
                'skipped': result['skipped'],
                'failed': result['failed']
            }
        )

        print(f"\nImport Summary:")
        print(f"  Job ID: {result['job_id']}")
        print(f"  Imported: {result['imported']}")
        print(f"  Skipped (duplicates): {result['skipped']}")
        print(f"  Failed: {result['failed']}")

        if result['doc_ids']:
            print(f"\nImported document IDs:")
            for doc_id in result['doc_ids'][:10]:
                print(f"  - {doc_id}")
            if len(result['doc_ids']) > 10:
                print(f"  ... and {len(result['doc_ids']) - 10} more")

    except Exception as e:
        logger.error(f"Import failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == '__main__':
    main()
