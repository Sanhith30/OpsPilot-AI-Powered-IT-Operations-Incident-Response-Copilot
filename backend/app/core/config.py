from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "OpsPilot API"
    app_version: str = "0.1.0"
    environment: str = "development"

    # Database
    db_host: str = Field(default="localhost", validation_alias=AliasChoices("db_host", "postgres_host"))
    db_port: int = Field(default=5432, validation_alias=AliasChoices("db_port", "postgres_port"))
    db_name: str = Field(default="opspilot", validation_alias=AliasChoices("db_name", "postgres_db"))
    db_user: str = Field(default="postgres", validation_alias=AliasChoices("db_user", "postgres_user"))
    db_password: str = Field(default="postgres", validation_alias=AliasChoices("db_password", "postgres_password"))
    database_url: str | None = Field(default=None, validation_alias=AliasChoices("database_url", "db_url"))

    # Auth
    jwt_secret_key: str = "insecure_default_jwt_secret_key_32_bytes_long"
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
    vector_store_provider: str = "pinecone"
    pinecone_api_key: str | None = None
    pinecone_index_name: str = "opspilot-knowledge"
    pinecone_namespace: str = "opspilot"
    rag_top_k: int = 5
    rag_score_threshold: float = 0.65


    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
