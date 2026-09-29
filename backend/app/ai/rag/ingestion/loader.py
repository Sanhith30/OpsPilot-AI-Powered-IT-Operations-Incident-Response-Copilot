from pathlib import Path

from app.ai.rag.schemas import KnowledgeDocument

SUPPORTED_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
}


class KnowledgeDocumentLoader:
    """
    Loads supported local knowledge-base documents.
    PDF and other formats will be added in later ingestion steps.
    """

    def load_file(
        self,
        path: str | Path,
        *,
        source_type: str = "FILE",
    ) -> KnowledgeDocument:
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"Knowledge document not found: {file_path}"
            )

        if not file_path.is_file():
            raise ValueError(
                f"Knowledge path is not a file: {file_path}"
            )

        extension = file_path.suffix.lower()

        if extension not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported knowledge document type: {extension}"
            )

        content = file_path.read_text(
            encoding="utf-8"
        )

        title = file_path.stem.replace(
            "_",
            " ",
        ).replace(
            "-",
            " ",
        ).strip()

        return KnowledgeDocument(
            document_id=file_path.as_posix(),
            source_type=source_type,
            source_name=file_path.name,
            title=title,
            content=content,
            metadata={
                "file_extension": extension,
            },
        )
