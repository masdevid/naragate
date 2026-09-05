import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from functools import lru_cache

class Settings(BaseSettings):
    # Required
    SECTORS_API_KEY: str = Field(default="", validation_alias="SECTORS_API_KEY")

    # LLM Provider (OpenAI-compatible)
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", validation_alias="OLLAMA_BASE_URL")
    # Empty by default: the model is configured via the web UI settings page.
    OLLAMA_MODEL: str = Field(default="", validation_alias="OLLAMA_MODEL")

    # Pi Agent harness gateway. When set, all LLM calls are routed through the
    # Pi Coding Agent harness (pi-agent service) instead of calling the LLM
    # endpoint directly. The pi-agent maps each agent role to its .pi/skills/*
    # definition and runs it through the Pi CLI.
    PI_AGENT_URL: str = Field(default="", validation_alias="PI_AGENT_URL")

    # Per-agent model overrides (optional, defaults to OLLAMA_MODEL)
    CLAIM_PARSER_MODEL: str = Field(default="", validation_alias="CLAIM_PARSER_MODEL")
    SKEPTIC_MODEL: str = Field(default="", validation_alias="SKEPTIC_MODEL")
    SCORER_MODEL: str = Field(default="", validation_alias="SCORER_MODEL")

    # Ports
    FRONTEND_PORT: int = Field(default=4273, validation_alias="FRONTEND_PORT")
    BACKEND_PORT: int = Field(default=5678, validation_alias="BACKEND_PORT")

    # Redis (evidence cache only)
    REDIS_URL: str = Field(default="redis://localhost:6379", validation_alias="REDIS_URL")

    # SQLite
    DATABASE_URL: str = Field(default="sqlite:///./data/naragate.db", validation_alias="DATABASE_URL")

    # Cache TTLs
    EVIDENCE_CACHE_TTL_COMPANY: int = Field(default=86400, validation_alias="EVIDENCE_CACHE_TTL_COMPANY")
    EVIDENCE_CACHE_TTL_DAILY: int = Field(default=3600, validation_alias="EVIDENCE_CACHE_TTL_DAILY")

    # Curated stocks
    CURATED_STOCKS: list[str] = Field(default=["BBCA", "BBRI", "BMRI", "TLKM", "UNVR"], validation_alias="CURATED_STOCKS")

    # Credit budget for Sectors API
    CREDIT_BUDGET: int = Field(default=600, validation_alias="CREDIT_BUDGET")

    @field_validator("SECTORS_API_KEY", mode="before")
    @classmethod
    def resolve_api_key(cls, v: str) -> str:
        if v:
            return v
        # Try .env file
        env_path = Path(".env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("SECTORS_API_KEY="):
                    return line.split("=", 1)[1].strip()
        # Try git repo secret file
        secret_path = Path(".secrets/sectors_api_key")
        if secret_path.exists():
            return secret_path.read_text().strip()
        # Try global secret
        global_secret = Path(os.path.expanduser("~/.secrets/sectors_api_key"))
        if global_secret.exists():
            return global_secret.read_text().strip()
        # No key found anywhere: return empty so the app still starts.
        # The key can be set later via the web UI settings page.
        return ""

    @property
    def claim_parser_model(self) -> str:
        return self.CLAIM_PARSER_MODEL or self.OLLAMA_MODEL

    @property
    def skeptic_model(self) -> str:
        return self.SKEPTIC_MODEL or self.OLLAMA_MODEL

    @property
    def scorer_model(self) -> str:
        return self.SCORER_MODEL or self.OLLAMA_MODEL

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
