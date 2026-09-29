from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):

    @abstractmethod
    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple documents.
        """
        raise NotImplementedError

    @abstractmethod
    def embed_query(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate an embedding for a search query.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def dimension(self) -> int:
        raise NotImplementedError
