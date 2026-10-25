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
    GROQ_MODEL: str = "qwen/qwen3.8-27b"

    # RAG Settings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    RETRIEVAL_TAU: float = 0.58
    TOP_K_CHUNKS: int = 4
    VECTOR_DB_TYPE: str = "chroma"  # "chroma" | "pinecone"
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "mutual-fund-facts"
    PINECONE_ENVIRONMENT: str = "us-east-1"

    # Storage Paths
    DATA_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data"))
    FACTS_DB_PATH: str = os.path.join(DATA_DIR, "index", "facts.db")
    CHROMA_DIR: str = os.path.join(DATA_DIR, "index", "chroma")
    SESSION_TTL_DAYS: int = 7

    @field_validator("DATA_DIR", mode="after")
    @classmethod
    def resolve_data_dir(cls, v: str) -> str:
        if not os.path.isabs(v):
            return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data"))
        return v

    @field_validator("FACTS_DB_PATH", mode="after")
    @classmethod
    def resolve_facts_db(cls, v: str) -> str:
        if not os.path.isabs(v):
            return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/index/facts.db"))
        return v

    @field_validator("CHROMA_DIR", mode="after")
    @classmethod
    def resolve_chroma_dir(cls, v: str) -> str:
        if not os.path.isabs(v):
            return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/index/chroma"))
        return v

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
