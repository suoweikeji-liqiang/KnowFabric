"""CLI script for chunk generation."""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from packages.core.config import settings
from packages.core.logging import setup_logging
from packages.db.session import SessionLocal
from packages.chunking.service import ChunkingService
import logging

setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Generate chunks from pages')
    parser.add_argument('doc_id', help='Document ID to chunk')

    args = parser.parse_args()

    chunking_service = ChunkingService()
    db = SessionLocal()

    try:
        logger.info(f"Chunking document: {args.doc_id}")

        result = chunking_service.chunk_document(db, args.doc_id)

        logger.info(
            f"Chunking complete",
            extra={
                'job_id': result['job_id'],
                'doc_id': result['doc_id'],
                'chunks_created': result['chunks_created']
            }
        )

        print(f"\nChunking Summary:")
        print(f"  Job ID: {result['job_id']}")
        print(f"  Document ID: {result['doc_id']}")
        print(f"  Chunks Created: {result['chunks_created']}")

    except Exception as e:
        logger.error(f"Chunking failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == '__main__':
    main()
