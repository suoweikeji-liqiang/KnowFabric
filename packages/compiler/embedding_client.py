"""OpenAI-compatible embedding client for BGE-M3 via oMLX (local)."""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Optional
from urllib import error, request

OMLX_BASE_URL = os.environ.get("OMLX_BASE_URL", "http://localhost:7999")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "bge-m3-mlx-4bit")
EMBEDDING_DIM = 1024

CACHE_DIR = Path(os.environ.get("EMBEDDING_CACHE_DIR", "/tmp/knowfabric_embedding_cache"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _api_key() -> str:
    key = os.environ.get("OMLX_API_KEY", "")
    if not key:
        raise RuntimeError("OMLX_API_KEY env var not set; oMLX requires authentication")
    return key


def _cache_path(text: str, model: str) -> Path:
    h = hashlib.sha1(f"{model}::{text}".encode()).hexdigest()
    return CACHE_DIR / f"{h}.json"


def embed_one(text: str, *, model: str | None = None, retries: int = 3) -> list[float]:
    """Embed a single text. Caches result on disk by (model, text) hash."""
    model = model or EMBEDDING_MODEL
    cp = _cache_path(text, model)
    if cp.exists():
        return json.loads(cp.read_text())["embedding"]

    payload = {"model": model, "input": text}
    req = request.Request(
        f"{OMLX_BASE_URL.rstrip('/')}/v1/embeddings",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_api_key()}",
        },
        method="POST",
    )

    last_err: Optional[Exception] = None
    for attempt in range(retries):
        try:
            with request.urlopen(req, timeout=60) as resp:
                body = json.loads(resp.read())
            emb = body["data"][0]["embedding"]
            if len(emb) != EMBEDDING_DIM:
                raise RuntimeError(f"Expected dim {EMBEDDING_DIM}, got {len(emb)}")
            cp.write_text(json.dumps({"model": model, "text": text, "embedding": emb}))
            return emb
        except (error.URLError, error.HTTPError, KeyError, json.JSONDecodeError) as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(0.5 * (attempt + 1))
            continue

    raise RuntimeError(f"embedding failed after {retries} retries: {last_err}")


def embed_batch(texts: list[str], *, model: str | None = None) -> list[list[float]]:
    """Embed multiple texts sequentially."""
    return [embed_one(t, model=model) for t in texts]
