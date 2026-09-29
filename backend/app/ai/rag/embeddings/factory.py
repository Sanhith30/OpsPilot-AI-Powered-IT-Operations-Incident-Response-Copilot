import hashlib
from app.ai.rag.embeddings.base import EmbeddingProvider
from app.ai.rag.embeddings.gemini import GeminiEmbeddingProvider
from app.core.config import settings


class MockEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dimension: int = 1536):
        self._dim = dimension

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        h = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16)
        return [float((h >> (i % 64)) & 1) for i in range(self._dim)]

    @property
    def model_name(self) -> str:
        return "mock-embedding"

    @property
    def dimension(self) -> int:
        return self._dim


def create_embedding_provider() -> EmbeddingProvider:
    provider = settings.embedding_provider.lower()

    if provider == "gemini" and settings.gemini_api_key:
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

    return MockEmbeddingProvider(dimension=settings.embedding_dimensions)
