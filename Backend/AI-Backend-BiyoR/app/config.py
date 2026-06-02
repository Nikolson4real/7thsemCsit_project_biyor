"""
Configuration management for BiyoR AI Rules Engine.
All settings are loaded from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Google AI Studio Configuration
    google_api_key: str = Field(..., description="Google AI Studio API key")
    gemini_primary_model: str = Field(
        default="models/gemini-1.5-flash",
        description="Primary Gemini model for rules engine (1.5-flash is more stable)"
    )
    gemini_fallback_model: str = Field(
        default="models/gemini-1.5-flash-8b",
        description="Fallback Gemini model if primary fails (smaller, faster)"
    )
    google_embeddings_model: str = Field(
        default="models/text-embedding-004",
        description="Google embeddings model from AI Studio"
    )
    
    # FAISS and Document Configuration
    faiss_index_path: Path = Field(
        default=Path("./data/faiss_index"),
        description="Path to store FAISS index files"
    )
    rulebooks_dir: Path = Field(
        default=Path("./data/rulebooks"),
        description="Directory containing Dandi Biyo rulebooks"
    )
    
    # RAG Pipeline Configuration
    retrieval_top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of top chunks to retrieve from FAISS"
    )
    chunk_size: int = Field(
        default=600,
        ge=200,
        le=1500,
        description="Size of document chunks in tokens"
    )
    chunk_overlap: int = Field(
        default=100,
        ge=0,
        le=300,
        description="Overlap between consecutive chunks"
    )
    
    # LLM Configuration
    llm_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Temperature for LLM generation (lower = more deterministic)"
    )
    llm_max_output_tokens: int = Field(
        default=2048,
        ge=256,
        le=8192,
        description="Maximum tokens in LLM response"
    )
    llm_timeout_seconds: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Timeout for LLM API calls"
    )
    
    # API Configuration
    api_version: str = Field(default="v1", description="API version prefix")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Groq API Configuration (for Chat Referee)
    groq_api_key: str = Field(
        default="",
        description="Groq API key for chat referee LLM"
    )
    groq_chat_model: str = Field(
        default="llama-3.1-8b-instant",
        description="Groq model for chat referee (fast, low-cost)"
    )
    
    # Session Configuration
    session_backend: str = Field(
        default="memory",
        description="Session storage backend: 'memory' or 'redis'"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
