"""Application configuration settings."""

from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/polymarket_scanner"
    )

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    # API Keys
    POLYMARKET_API_KEY: str = os.getenv("POLYMARKET_API_KEY", "")
    SEC_EDGAR_API_KEY: str = os.getenv("SEC_EDGAR_API_KEY", "")
    TRANSCRIPT_SERVICE_API_KEY: str = os.getenv("TRANSCRIPT_SERVICE_API_KEY", "")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Job Scheduler
    SCHEDULER_ENABLED: bool = True
    POLYMARKET_SYNC_INTERVAL: int = 3600  # 1 hour

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
