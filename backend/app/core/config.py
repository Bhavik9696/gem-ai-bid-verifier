import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "ComplianceOS — Core API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Base URLs and ports matching worksplit.md
    CORE_API_BASE_URL: str = "http://localhost:8000"
    CONNECTOR_API_BASE_URL: str = "http://localhost:8001"
    
    # Database
    DATABASE_URL: str = "postgresql://complianceos:complianceos@localhost:5432/complianceos"
    SQLITE_FALLBACK_URL: str = "sqlite:///./complianceos.db"
    
    # Redis & Storage
    REDIS_URL: str = "redis://localhost:6379/0"
    S3_ENDPOINT: str = "http://localhost:9000"
    
    # Demo Data Path
    DEMO_DATA_DIR: Path = Path(__file__).resolve().parent.parent.parent / "demo-data"
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://localhost:8001",
        "*"
    ]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
