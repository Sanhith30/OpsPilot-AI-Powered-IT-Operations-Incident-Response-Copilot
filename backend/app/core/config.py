from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "OpsPilot API"
    app_version: str = "0.1.0"
    environment: str = "development"

    # Database
    db_host: str
    db_port: int = 5432
    db_name: str
    db_user: str
    db_password: str

    # Auth
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    llm_provider: str = "mock"
    llm_model: str = "mock-model"
    llm_temperature: float = 0.0
    llm_timeout_seconds: int = 30
    gemini_api_key: str | None = None

    # RAG Settings
    rag_enabled: bool = True
    embedding_provider: str = "gemini"
    embedding_model: str = "gemini-embedding-2"
    embedding_dimensions: int = 1536
    pinecone_api_key: str | None = None
    pinecone_index_name: str = "opspilot-knowledge"
    pinecone_namespace: str = "opspilot"
    rag_top_k: int = 5
    rag_score_threshold: float = 0.65

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
