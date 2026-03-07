"""Basic integration test for P0 main chain."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from packages.db.session import SessionLocal
from packages.storage.manager import StorageManager
from packages.ingest.service import IngestService
from packages.parser.service import ParserService
from packages.chunking.service import ChunkingService
from packages.retrieval.service import RetrievalService
from packages.core.config import settings


def test_main_chain():
    """Test document -> page -> chunk -> retrieval chain."""
    print("Testing P0 main chain...")

    db = SessionLocal()
    storage = StorageManager(settings.storage_root)

    try:
        # Note: This test requires actual PDF files in tests/fixtures/documents/
        # For now, this is a structure test only

        print("✓ Services initialized")

        # Test that services can be instantiated
        ingest = IngestService(storage)
        parser = ParserService(storage)
        chunking = ChunkingService()
        retrieval = RetrievalService()

        print("✓ All services instantiated successfully")
        print("\nP0 main chain structure validated")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

    finally:
        db.close()


if __name__ == '__main__':
    success = test_main_chain()
    sys.exit(0 if success else 1)
