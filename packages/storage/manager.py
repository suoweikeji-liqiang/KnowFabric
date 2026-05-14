"""File storage helpers for immutable source documents."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path


class StorageManager:
    """Manage source document copies under a configured storage root."""

    def __init__(self, storage_root: str | Path):
        self.storage_root = Path(storage_root)
        self.documents_root = self.storage_root / "documents"
        self.documents_root.mkdir(parents=True, exist_ok=True)

    def calculate_file_hash(self, file_path: str | Path) -> str:
        digest = hashlib.sha256()
        with Path(file_path).open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    def store_document(self, file_path: str | Path, doc_id: str) -> str:
        source = Path(file_path)
        if not source.exists():
            raise FileNotFoundError(str(source))
        target = self.documents_root / doc_id / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copy2(source, target)
        return str(target.relative_to(self.storage_root))

    def get_document_path(self, storage_path: str | Path) -> Path:
        path = Path(storage_path)
        if path.is_absolute():
            return path
        return self.storage_root / path
