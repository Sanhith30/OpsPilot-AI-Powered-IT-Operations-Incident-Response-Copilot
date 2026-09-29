from __future__ import annotations

import hashlib
import math
from app.ai.rag.embeddings.base import EmbeddingProvider


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic mock embedding provider for testing and CI environments.
    Generates repeatable unit vectors without requiring external API keys.
    """

    def __init__(self, dimension: int = 768, model: str = "mock-embedding") -> None:
        self._dimension = dimension
        self._model = model

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimension(self) -> int:
        return self._dimension

    def _generate_vector(self, text: str) -> list[float]:
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vec = []
        for i in range(self._dimension):
            byte_val = h[i % len(h)]
            val = ((byte_val ^ (i & 0xFF)) - 128) / 128.0
            vec.append(val)
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [round(x / norm, 6) for x in vec]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._generate_vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._generate_vector(text)


TestEmbeddingProvider = MockEmbeddingProvider
