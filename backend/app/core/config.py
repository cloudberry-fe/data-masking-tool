"""
系统配置
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # 应用基本配置
    APP_NAME: str = "数据脱敏系统"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    API_V1_STR: str = "/api/v1"

    # 数据库配置
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/data_masking"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT配置
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production-please"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # 加密配置（用于加密数据库密码等敏感信息）
    ENCRYPTION_KEY: str = "your-32-byte-encryption-key-here"

    # HashData Lightning 配置
    HASHDATA_HOST: str = "localhost"
    HASHDATA_PORT: int = 5432
    HASHDATA_DATABASE: str = "hashdata"
    HASHDATA_USERNAME: str = "gpadmin"
    HASHDATA_PASSWORD: str = ""

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 104857600  # 100MB

    # CORS配置
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()
