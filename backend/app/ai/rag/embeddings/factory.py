from app.ai.rag.embeddings.base import EmbeddingProvider
from app.ai.rag.embeddings.gemini import GeminiEmbeddingProvider
from app.core.config import settings


def create_embedding_provider() -> EmbeddingProvider:
    provider = settings.embedding_provider.lower()

    if provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is required for Gemini embeddings"
            )

        api_key = (
            settings.gemini_api_key.get_secret_value()
            if hasattr(settings.gemini_api_key, "get_secret_value")
            else settings.gemini_api_key
        )

        return GeminiEmbeddingProvider(
            api_key=api_key,
            model=settings.embedding_model,
            dimension=settings.embedding_dimensions,
        )

    raise ValueError(
        f"Unsupported embedding provider: {settings.embedding_provider}"
    )
