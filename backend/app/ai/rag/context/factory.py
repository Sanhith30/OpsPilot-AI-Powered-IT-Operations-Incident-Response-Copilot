from app.ai.rag.context.builder import (
    RAGContextBuilder,
)


def create_rag_context_builder(
    *,
    max_context_characters: int = 12000,
) -> RAGContextBuilder:
    return RAGContextBuilder(
        max_context_characters=max_context_characters
    )
