from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)

from app.ai.rag.ingestion.ids import (
    create_chunk_id,
)
from app.ai.rag.schemas import (
    KnowledgeChunk,
    KnowledgeDocument,
)


class KnowledgeChunker:

    def __init__(
        self,
        *,
        chunk_size: int = 1200,
        chunk_overlap: int = 180,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError(
                "chunk_size must be positive"
            )
        if chunk_overlap < 0:
            raise ValueError(
                "chunk_overlap cannot be negative"
            )
        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size"
            )

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n## ",
                "\n### ",
                "\n#### ",
                "\n\n",
                "\n",
                ". ",
                " ",
                "",
            ],
        )

    def chunk(
        self,
        document: KnowledgeDocument,
        *,
        version_number: int,
    ) -> list[KnowledgeChunk]:
        raw_chunks = self.splitter.split_text(
            document.content
        )

        chunks: list[KnowledgeChunk] = []

        for index, content in enumerate(raw_chunks):
            cleaned_content = content.strip()
            if not cleaned_content:
                continue

            chunk_id = create_chunk_id(
                document_id=document.document_id,
                version_number=version_number,
                chunk_index=index,
                content=cleaned_content,
            )

            chunks.append(
                KnowledgeChunk(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    content=cleaned_content,
                    chunk_index=index,
                    version_number=version_number,
                    metadata={
                        "source_name": document.source_name,
                        "source_type": document.source_type,
                        "title": document.title,
                        "version_number": version_number,
                    },
                )
            )

        return chunks
