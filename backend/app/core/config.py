"""
Application Configuration
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration"""

    # Basic application configuration
    APP_NAME: str = "Cloudberry Data Management Console"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    API_V1_STR: str = "/api/v1"

    # Database configuration
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/data_masking"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT configuration
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production-please"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Encryption configuration (for sensitive data like database passwords)
    ENCRYPTION_KEY: str = "your-32-byte-encryption-key-here"

    # HashData Lightning configuration
    HASHDATA_HOST: str = "localhost"
    HASHDATA_PORT: int = 5432
    HASHDATA_DATABASE: str = "hashdata"
    HASHDATA_USERNAME: str = "gpadmin"
    HASHDATA_PASSWORD: str = ""

    # Log configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # File upload configuration
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 104857600  # 100MB

    # CORS configuration
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get configuration singleton"""
    return Settings()


settings = get_settings()
