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
    llm_compile_enabled: bool = False
    llm_api_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str | None = None
    llm_model: str | None = None
    llm_compile_timeout_seconds: int = 30
    llm_compile_context_radius: int = 1
    llm_backend_config_path: str | None = None
    llm_backend_name: str | None = None
    llm_enabled_types: str = "maintenance_procedure,application_guidance"

    class Config:
        env_file = str(ENV_FILE)


settings = Settings()
