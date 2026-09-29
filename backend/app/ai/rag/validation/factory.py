from app.ai.rag.validation.citation_validator import CitationValidator


def create_citation_validator() -> CitationValidator:
    """
    Factory to construct CitationValidator instance.
    """
    return CitationValidator()
