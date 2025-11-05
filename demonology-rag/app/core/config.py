import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/daemonology"
    OPENAI_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    LLM_MODEL: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    DATA_DIR: str = "./data"
    INDEX_DIR: str = "./indexes"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

