"""Core configuration management."""
from pathlib import Path

from pydantic_settings import BaseSettings


ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    """Application settings."""

    database_url: str = "postgresql://knowfabric:knowfabric@localhost:5432/knowfabric"
    storage_root: str = "./storage/documents"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    worker_concurrency: int = 4
    log_level: str = "INFO"

    class Config:
        env_file = str(ENV_FILE)


settings = Settings()
