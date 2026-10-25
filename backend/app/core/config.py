import os
import json
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Primary LLM Settings (Groq)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # RAG Settings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    RETRIEVAL_TAU: float = 0.70
    TOP_K_CHUNKS: int = 4

    # Storage Paths
    DATA_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data"))
    FACTS_DB_PATH: str = os.path.join(DATA_DIR, "index", "facts.db")
    CHROMA_DIR: str = os.path.join(DATA_DIR, "index", "chroma")
    SESSION_TTL_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
