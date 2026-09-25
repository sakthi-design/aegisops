"""
Application settings and configuration management using Pydantic Settings.
"""
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Automated Incident Narrative Synthesis Platform"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    API_V1_STR: str = "/api"
    
    # Database
    DATABASE_URL: str = "sqlite:///./data/incident_platform.db"
    
    # LLM Settings & Provider Selection (supports "mock", "gemini", "openai", "ollama")
    LLM_PROVIDER: str = "mock"  # Defaults to high-precision deterministic mock provider for reproducible testing
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "gemini-1.5-pro"
    LLM_TEMPERATURE: float = 0.1
    MAX_CRITIC_RETRIES: int = 3
    
    # Security & Sanitization
    PII_MASKING_ENABLED: bool = True
    SECRET_MASKING_ENABLED: bool = True
    AUDIT_LOG_ENABLED: bool = True
    MAX_UPLOAD_SIZE_BYTES: int = 50 * 1024 * 1024  # 50MB
    
    # RAG Settings
    KNOWLEDGE_BASE_DIR: str = "data/knowledge_base"
    RAG_TOP_K: int = 4
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
