"""Application configuration settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Core application settings loaded from environment or .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    HOST: str = "127.0.0.1"
    PORT: int = 8000
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
        ]
    )

    # Auth
    AUTH_DISABLED: bool = True
    JWT_SECRET: str = "supersecretdevkeyatleast32characterslong12345"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./clinical_transcription.db"

    # ASR (Whisper)
    WHISPER_MODEL: str = "small.en"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"

    # LLM
    LLM_PROVIDER: str = "mock"
    LLM_MODEL: str = "claude-3-5-sonnet-20241022"
    ANTHROPIC_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None

    # Storage and retention
    MAX_AUDIO_SECONDS: int = 30
    RETENTION_DAYS: int = 30
    AUDIO_STORAGE_PATH: str = "./audio_storage"


settings = Settings()
