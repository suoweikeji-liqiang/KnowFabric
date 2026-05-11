"""H1: embedding_client tests (docs/39 §4.3)."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_embed_one_caches_result():
    """Mock urlopen returns 1024-dim vector; second call uses cache."""
    fake_emb = [0.0] * 1024

    with patch("packages.compiler.embedding_client._api_key", return_value="test-key"):
        with patch("packages.compiler.embedding_client.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = (
                b'{"data":[{"embedding":[' + b",".join(str(x).encode() for x in fake_emb) + b']}]}'
            )
            mock_resp.__enter__.return_value = mock_resp
            mock_urlopen.return_value = mock_resp

            from packages.compiler.embedding_client import embed_one

            # Clear cache
            import shutil
            from packages.compiler.embedding_client import CACHE_DIR
            if CACHE_DIR.exists():
                shutil.rmtree(CACHE_DIR)
            CACHE_DIR.mkdir()

            result1 = embed_one("test_param", model="bge-m3")
            assert len(result1) == 1024
            assert mock_urlopen.call_count == 1

            # Second call: should use disk cache, no HTTP request
            result2 = embed_one("test_param", model="bge-m3")
            assert len(result2) == 1024
            assert mock_urlopen.call_count == 1  # still 1, cache hit


def test_embed_batch_returns_correct_count():
    fake_emb = [0.0] * 1024
    with patch("packages.compiler.embedding_client.embed_one", return_value=fake_emb):
        from packages.compiler.embedding_client import embed_batch
        results = embed_batch(["a", "b", "c"])
        assert len(results) == 3
        for r in results:
            assert len(r) == 1024
