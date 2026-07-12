from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "Enterprise Knowledge Base"
    APP_VERSION: str = "1.1.0"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql://postgres:123456@localhost:5432/kiro"
    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "kiro-documents"

    CORS_ORIGINS: list = ["http://localhost:5120", "http://localhost:3000"]

    # SSO配置
    DINGTALK_CLIENT_ID: str = ""
    DINGTALK_CLIENT_SECRET: str = ""
    DINGTALK_REDIRECT_URI: str = "http://localhost:8000/api/v1/sso/dingtalk/callback"

    WECHATWORK_CORPID: str = ""
    WECHATWORK_SECRET: str = ""
    WECHATWORK_REDIRECT_URI: str = "http://localhost:8000/api/v1/sso/wechatwork/callback"

    FEISHU_CLIENT_ID: str = ""
    FEISHU_CLIENT_SECRET: str = ""
    FEISHU_REDIRECT_URI: str = "http://localhost:8000/api/v1/sso/feishu/callback"

    # FAISS向量数据库配置
    FAISS_INDEX_PATH: str = "./data/faiss"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
