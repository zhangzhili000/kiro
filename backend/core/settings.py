"""
Kiro AI Platform - System Settings

This module provides system configuration using Pydantic.
"""
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """System Settings"""
    
    # Application Info
    APP_NAME: str = "Kiro AI Platform"
    APP_VERSION: str = "1.1.0"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "postgresql://kiro:kiro123@localhost:5432/kiro"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "kiro"
    MINIO_SECRET_KEY: str = "kiro123"
    MINIO_BUCKET: str = "kiro-documents"
    MINIO_SECURE: bool = False
    
    # Commercial Features (License Controlled)
    MULTI_TENANT_ENABLED: bool = False      # 多租户隔离
    CROSS_ORG_SHARING_ENABLED: bool = False # 跨机构共享
    AUDIT_LOGGING_ENABLED: bool = False     # 审计日志
    SSO_ENABLED: bool = False               # SSO集成
    
    # License
    LICENSE_FILE: str = "license.kiro"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: List[str] = [
        ".pdf", ".doc", ".docx", ".txt", ".md",
        ".xls", ".xlsx", ".ppt", ".pptx"
    ]
    
    # Document Processing
    PARSER_CHUNK_SIZE: int = 512
    PARSER_CHUNK_OVERLAP: int = 50
    VECTOR_DIMENSION: int = 1536
    
    # LLM Settings
    DEFAULT_LLM_MODEL: str = "gpt-3.5-turbo"
    DEFAULT_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get system settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment"""
    global _settings
    _settings = Settings()
    return _settings
