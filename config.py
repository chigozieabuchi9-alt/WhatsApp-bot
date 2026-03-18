"""
Application configuration using Pydantic Settings.
"""
from functools import lru_cache
from typing import Optional

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # Application
    APP_NAME: str = "WhatsAppBot"
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = Field(..., min_length=32)
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    TWILIO_WEBHOOK_URL: str
    
    # Database
    DATABASE_URL: PostgresDsn
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_NAME: str = "whatsapp_bot"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    
    # Redis
    REDIS_URL: RedisDsn
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Celery
    CELERY_BROKER_URL: RedisDsn
    CELERY_RESULT_BACKEND: RedisDsn
    CELERY_WORKERS: int = 2
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 30
    RATE_LIMIT_REQUESTS_PER_HOUR: int = 200
    RATE_LIMIT_BLOCK_DURATION: int = 300
    
    # User Tiers
    TIER_GUEST_DAILY_LIMIT: int = 20
    TIER_USER_DAILY_LIMIT: int = 100
    TIER_PREMIUM_DAILY_LIMIT: int = 500
    TIER_ADMIN_UNLIMITED: bool = True
    
    # External APIs
    OPENWEATHERMAP_API_KEY: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None
    EXCHANGE_RATE_API_KEY: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    SENTRY_DSN: Optional[str] = None
    
    # Feature Flags
    ENABLE_GAMES: bool = True
    ENABLE_REMINDERS: bool = True
    ENABLE_NEWS: bool = True
    ENABLE_WEATHER: bool = True
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for migrations."""
        return str(self.DATABASE_URL).replace(
            "postgresql+asyncpg://", "postgresql://"
        )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
