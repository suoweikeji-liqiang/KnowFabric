"""Core configuration management."""
from pathlib import Path

from pydantic_settings import BaseSettings


ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR / ".env"
ENV_LLM_LOCAL = ROOT_DIR / ".env.llm.local"

# Load .env.llm.local if present (MiMo API keys etc.)
if ENV_LLM_LOCAL.exists():
    with open(ENV_LLM_LOCAL, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and value and key not in __import__("os").environ:
                    __import__("os").environ[key] = value


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
    llm_max_concurrent: int = 8
    llm_max_rpm: int = 60
    llm_max_retries: int = 5
    extraction_doc_concurrency: int = 8

    class Config:
        env_file = str(ENV_FILE)


settings = Settings()
