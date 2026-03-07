"""CLI script for rerunning document processing."""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from packages.core.config import settings
from packages.core.logging import setup_logging
from packages.db.session import SessionLocal
from packages.storage.manager import StorageManager
from packages.parser.service import ParserService
from packages.chunking.service import ChunkingService
import logging

setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Rerun document processing')
    parser.add_argument('doc_id', help='Document ID to reprocess')
    parser.add_argument('--stage', choices=['parse', 'chunk', 'all'], default='all',
                       help='Stage to rerun')

    args = parser.parse_args()
    db = SessionLocal()

    try:
        if args.stage in ['parse', 'all']:
            logger.info(f"Rerunning parse for: {args.doc_id}")
            storage = StorageManager(settings.storage_root)
            parser_service = ParserService(storage)
            result = parser_service.parse_document(db, args.doc_id)
            print(f"Parse complete: {result['pages_created']} pages")

        if args.stage in ['chunk', 'all']:
            logger.info(f"Rerunning chunk for: {args.doc_id}")
            chunking_service = ChunkingService()
            result = chunking_service.chunk_document(db, args.doc_id)
            print(f"Chunk complete: {result['chunks_created']} chunks")

        print(f"\nReprocessing complete for: {args.doc_id}")

    except Exception as e:
        logger.error(f"Reprocessing failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == '__main__':
    main()
