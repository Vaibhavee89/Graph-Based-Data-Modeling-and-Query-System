"""Application configuration using pydantic-settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from pathlib import Path
from typing import Optional, Union


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Graph Data Modeling System"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/graphdb"

    # API Keys
    anthropic_api_key: Optional[str] = None   # optional: Groq alone is enough
    groq_api_key: Optional[str] = None

    # LLM Settings
    llm_model: str = "claude-haiku-4-5-20251001"
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.0

    # Groq fallback settings
    groq_model: str = "openai/gpt-oss-120b"  # override with GROQ_MODEL; check console.groq.com for current models
    use_groq_fallback: bool = True
    # Built-in sample data shown until a user connects their own database
    sample_data_dir: str = str(Path(__file__).resolve().parent.parent / "sample_data")

    # Query Settings
    query_timeout: int = 30  # seconds
    max_query_results: int = 1000
    rate_limit_per_minute: int = 10
    # Only enable behind a trusted reverse proxy (Railway, nginx): X-Forwarded-For is spoofable otherwise
    trust_proxy_headers: bool = False

    # Graph Settings
    initial_node_limit: int = 500
    max_expansion_depth: int = 2
    graph_pickle_path: str = "backend/graph.pickle"

    # Bring-your-own-database connections
    access_code: Optional[str] = None           # if set, required to open a connection
    allow_private_hosts: bool = False           # allow localhost / private IPs (local dev only)
    allow_sqlite_connections: bool = False      # sqlite URLs read server-side files (local dev/tests only)
    connect_rate_limit_per_minute: int = 5
    session_ttl_minutes: int = 30
    max_sessions: int = 20
    max_tables: int = 100
    max_rows_per_table: int = 200
    max_graph_nodes: int = 5000

    # CORS
    cors_origins: Union[list[str], str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            # Split comma-separated string into list
            return [origin.strip() for origin in v.split(',')]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()
