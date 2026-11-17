"""
Application Configuration Module

Centralized configuration management using Pydantic Settings.
All settings are loaded from environment variables with validation.
"""

from functools import lru_cache
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ============================================
    # APPLICATION
    # ============================================
    APP_NAME: str = "Translator Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # ============================================
    # DATABASE
    # ============================================
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://translator:translator@localhost:5432/translator_db",
        description="PostgreSQL async connection string",
    )
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600

    # ============================================
    # REDIS
    # ============================================
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string",
    )
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5

    # ============================================
    # SECURITY
    # ============================================
    SECRET_KEY: str = Field(
        default="your-super-secret-key-change-in-production-min-32-chars",
        description="JWT signing secret key",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12

    # ============================================
    # CORS
    # ============================================
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ],
        description="Allowed CORS origins",
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # ============================================
    # AI MODELS
    # ============================================
    MODEL_CACHE_DIR: str = "./models"
    INDIC_TRANS2_MODEL_PATH: str = "./models/indictrans2"
    WHISPER_MODEL_PATH: str = "./models/whisper"
    MODEL_DEVICE: str = "cpu"
    INFERENCE_BATCH_SIZE: int = 1
    MAX_SEQ_LENGTH: int = 512
    ENABLE_INT8_QUANTIZATION: bool = True
    CPU_THREADS: int = 4

    # ============================================
    # INFERENCE QUEUE
    # ============================================
    MAX_CONCURRENT_INFERENCE: int = 4
    INFERENCE_TIMEOUT: int = 30
    INFERENCE_QUEUE_MAX_SIZE: int = 100

    # ============================================
    # CACHE TTL (seconds)
    # ============================================
    TRANSLATION_CACHE_TTL: int = 3600
    GLOSSARY_CACHE_TTL: int = 7200
    SESSION_CACHE_TTL: int = 1800

    # ============================================
    # WEBSOCKET
    # ============================================
    WS_PING_INTERVAL: int = 30
    WS_PING_TIMEOUT: int = 10
    WS_MAX_MESSAGE_SIZE: int = 1048576  # 1MB

    # ============================================
    # RATE LIMITING
    # ============================================
    RATE_LIMIT_REQUESTS: int = 60
    RATE_LIMIT_WINDOW: int = 60

    # ============================================
    # LOGGING
    # ============================================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # ============================================
    # FRONTEND (Vite env vars)
    # ============================================
    VITE_API_URL: str = "http://localhost:8000"
    VITE_WS_URL: str = "ws://localhost:8000"
    VITE_APP_TITLE: str = "Translator Platform"

    # ============================================
    # ADMIN INITIALIZATION
    # ============================================
    INIT_ADMIN_EMAIL: str = "admin@translator.local"
    INIT_ADMIN_PASSWORD: str = "change-me-immediately"
    INIT_ADMIN_FULL_NAME: str = "System Administrator"

    # ============================================
    # DOMAINS & LANGUAGES
    # ============================================
    DEFAULT_DOMAINS: List[str] = Field(
        default=["technology", "medical", "general"],
        description="Default conversation domains",
    )
    SUPPORTED_LANGUAGES: List[str] = Field(
        default=["en", "kn", "hi", "ml", "ta"],
        description="Supported language codes",
    )
    DEFAULT_SOURCE_LANG: str = "en"
    DEFAULT_TARGET_LANG: str = "kn"

    @field_validator("SUPPORTED_LANGUAGES", mode="before")
    @classmethod
    def parse_languages(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            return [lang.strip() for lang in v.split(",")]
        return v

    @field_validator("DEFAULT_DOMAINS", mode="before")
    @classmethod
    def parse_domains(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            return [domain.strip() for domain in v.split(",")]
        return v

    # ============================================
    # PROPERTIES
    # ============================================
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic migrations."""
        return self.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()