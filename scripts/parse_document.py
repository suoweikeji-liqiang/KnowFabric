"""CLI script for parsing documents."""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from packages.core.config import settings
from packages.core.logging import setup_logging
from packages.db.session import SessionLocal
from packages.storage.manager import StorageManager
from packages.parser.service import ParserService
import logging

setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Parse documents and generate pages')
    parser.add_argument('doc_id', help='Document ID to parse')

    args = parser.parse_args()

    storage = StorageManager(settings.storage_root)
    parser_service = ParserService(storage)
    db = SessionLocal()

    try:
        logger.info(f"Parsing document: {args.doc_id}")

        result = parser_service.parse_document(db, args.doc_id)

        logger.info(
            f"Parse complete",
            extra={
                'job_id': result['job_id'],
                'doc_id': result['doc_id'],
                'pages_created': result['pages_created']
            }
        )

        print(f"\nParse Summary:")
        print(f"  Job ID: {result['job_id']}")
        print(f"  Document ID: {result['doc_id']}")
        print(f"  Pages Created: {result['pages_created']}")

    except Exception as e:
        logger.error(f"Parse failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == '__main__':
    main()
