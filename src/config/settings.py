import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    # Application Config
    APP_NAME: str = os.getenv("APP_NAME", "AI Supply Chain Risk Monitor")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    PORT: int = int(os.getenv("PORT", "8501"))

    # LLM Settings (Primary: Groq API)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq").strip().lower()
    LLM_MODEL: str = os.getenv("LLM_MODEL", "groq/compound").strip()
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    COHERE_API_KEY: Optional[str] = os.getenv("COHERE_API_KEY")
    HUGGINGFACEHUB_API_TOKEN: Optional[str] = os.getenv("HUGGINGFACEHUB_API_TOKEN")

    # Embeddings Settings (Primary: Hugging Face API / BAAI/bge-small-en-v1.5)
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "huggingface").strip().lower()
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5").strip()


    # RAG Config
    VECTOR_DB: str = os.getenv("VECTOR_DB", "chroma").strip().lower()
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "supply_chain_risk_monitor").strip()
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    TOP_K: int = int(os.getenv("TOP_K", "5"))
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./chroma_db").strip()

    # Relational Database Config
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./supply_chain_risk.db").strip()
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "supply_chain_db")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    # LangSmith Observability Config
    LANGSMITH_API_KEY: Optional[str] = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_TRACING: bool = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "Supply-Chain-Risk-Monitor")
    LANGSMITH_ENDPOINT: str = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

    # Directories Config
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "data/uploads").strip()
    EXPORT_DIR: str = os.getenv("EXPORT_DIR", "data/exports").strip()
    RAW_FEED_DIR: str = os.getenv("RAW_FEED_DIR", "data/raw_feed_snapshots").strip()

    # External Feed Base URLs
    GDELT_BASE_URL: str = os.getenv("GDELT_BASE_URL", "https://api.gdeltproject.org/api/v2").strip()
    NOAA_BASE_URL: str = os.getenv("NOAA_BASE_URL", "https://api.weather.gov/alerts/active").strip()
    USGS_BASE_URL: str = os.getenv("USGS_BASE_URL", "https://earthquake.usgs.gov/fdsnws/event/1").strip()
    RELIEFWEB_BASE_URL: str = os.getenv("RELIEFWEB_BASE_URL", "https://api.reliefweb.int/v1").strip()
    NOMINATIM_BASE_URL: str = os.getenv("NOMINATIM_BASE_URL", "https://nominatim.openstreetmap.org").strip()

    # Scoring & Thresholds Settings
    REFRESH_INTERVAL_MINUTES: int = int(os.getenv("REFRESH_INTERVAL_MINUTES", "30"))
    HIGH_RISK_THRESHOLD: float = float(os.getenv("HIGH_RISK_THRESHOLD", "80"))
    MEDIUM_RISK_THRESHOLD: float = float(os.getenv("MEDIUM_RISK_THRESHOLD", "60"))
    LOW_RISK_THRESHOLD: float = float(os.getenv("LOW_RISK_THRESHOLD", "30"))
    REQUIRE_HUMAN_APPROVAL: bool = os.getenv("REQUIRE_HUMAN_APPROVAL", "true").lower() == "true"
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))

# Global Settings Singleton
settings = Settings()
