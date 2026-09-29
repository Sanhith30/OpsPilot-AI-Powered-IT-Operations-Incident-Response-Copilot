from pathlib import Path

from app.ai.rag.ingestion.chunker import (
    KnowledgeChunker,
)
from app.ai.rag.ingestion.ids import (
    create_content_hash,
    create_document_id,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.ai.rag.ingestion.loader import (
    KnowledgeDocumentLoader,
)
from app.ai.rag.ingestion.normalizer import (
    KnowledgeDocumentNormalizer,
)
from app.ai.rag.schemas import (
    KnowledgeChunk,
    KnowledgeDocument,
)
from app.ai.rag.vectorstore.base import (
    VectorStore,
)
from app.models.knowledge_document import (
    KnowledgeDocument as KnowledgeDocumentModel,
)
from app.models.knowledge_document_version import (
    KnowledgeDocumentVersion,
)
from app.repositories.knowledge_document_repository import (
    KnowledgeDocumentRepository,
)
from app.repositories.knowledge_document_version_repository import (
    KnowledgeDocumentVersionRepository,
)


class KnowledgeIngestionService:

    def __init__(
        self,
        *,
        loader: KnowledgeDocumentLoader,
        normalizer: KnowledgeDocumentNormalizer,
        chunker: KnowledgeChunker,
        vector_store: VectorStore,
        document_repository: KnowledgeDocumentRepository,
        version_repository: KnowledgeDocumentVersionRepository,
        db,
    ) -> None:
        self.loader = loader
        self.normalizer = normalizer
        self.chunker = chunker
        self.vector_store = vector_store
        self.document_repository = document_repository
        self.version_repository = version_repository
        self.db = db

    def prepare_file(
        self,
        path: str | Path,
        *,
        source_type: str = "FILE",
    ) -> KnowledgeDocument:
        document = self.loader.load_file(
            path,
            source_type=source_type,
        )

        document = self.normalizer.normalize(
            document
        )

        document_id = create_document_id(
            source_type=source_type,
            source_name=document.source_name,
        )

        content_hash = create_content_hash(
            document.content
        )

        return document.model_copy(
            update={
                "document_id": document_id,
                "content_hash": content_hash,
            }
        )

    def _get_or_create_document(
        self,
        document: KnowledgeDocument,
        *,
        actor_user_id: int | None = None,
    ) -> KnowledgeDocumentModel:
        existing = (
            self.document_repository.get_by_source(
                source_type=document.source_type,
                source_name=document.source_name,
            )
        )

        if existing is not None:
            return existing

        model = KnowledgeDocumentModel(
            source_type=document.source_type,
            source_name=document.source_name,
            title=document.title,
            status="ACTIVE",
        )

        self.document_repository.add(model)
        self.db.flush()

        return model

    def _get_latest_version_number(
        self,
        document_id: int,
    ) -> int:
        latest = (
            self.version_repository.get_latest(
                document_id
            )
        )

        if latest is None:
            return 0

        return latest.version_number

    def _create_version(
        self,
        *,
        document_model: KnowledgeDocumentModel,
        document: KnowledgeDocument,
        actor_user_id: int | None,
    ) -> KnowledgeDocumentVersion:
        latest_number = (
            self._get_latest_version_number(
                document_model.document_id
            )
        )

        version = KnowledgeDocumentVersion(
            document_id=document_model.document_id,
            version_number=latest_number + 1,
            content_hash=document.content_hash,
            content=document.content,
            ingestion_status="PENDING",
            created_by=actor_user_id,
        )

        self.version_repository.add(version)
        self.db.flush()

        return version

    def ingest_file(
        self,
        path: str | Path,
        *,
        source_type: str = "FILE",
        actor_user_id: int | None = None,
    ) -> dict:
        document = self.prepare_file(
            path,
            source_type=source_type,
        )

        document_model = (
            self._get_or_create_document(
                document,
                actor_user_id=actor_user_id,
            )
        )

        latest = (
            self.version_repository.get_latest(
                document_model.document_id
            )
        )

        # --------------------------------------------------
        # Same content: nothing to do.
        # --------------------------------------------------
        if (
            latest is not None
            and latest.content_hash == document.content_hash
        ):
            if latest.ingestion_status == "COMPLETED":
                return {
                    "status": "UNCHANGED",
                    "document_id": document_model.document_id,
                    "version_id": latest.version_id,
                    "version_number": latest.version_number,
                    "chunk_count": latest.chunk_count,
                }
            version = latest
        else:
            version = self._create_version(
                document_model=document_model,
                document=document,
                actor_user_id=actor_user_id,
            )

        version.ingestion_status = "PROCESSING"
        self.db.commit()

        try:
            # ----------------------------------------------
            # Create version-specific chunks.
            # ----------------------------------------------
            domain_document = document

            chunks = self.chunker.chunk(
                domain_document,
                version_number=version.version_number,
            )

            version.chunk_count = len(chunks)
            version.embedding_model = self._embedding_model_name()
            version.embedding_dimensions = self._embedding_dimensions()

            self.db.commit()

            # ----------------------------------------------
            # Write new vectors FIRST.
            # ----------------------------------------------
            self.vector_store.add_chunks(chunks)

            # ----------------------------------------------
            # New vectors exist successfully.
            # Mark the version complete.
            # ----------------------------------------------
            version.ingestion_status = "COMPLETED"
            document_model.current_version_id = version.version_id

            self.db.commit()

            # ----------------------------------------------
            # Old vectors may now be cleaned up.
            # ----------------------------------------------
            if (
                latest is not None
                and latest.version_number != version.version_number
            ):
                try:
                    self.vector_store.delete_document_version(
                        document.document_id,
                        latest.version_number,
                    )
                except Exception:
                    # Cleanup failure should not invalidate
                    # an already successful new version.
                    pass

            return {
                "status": "INGESTED",
                "document_id": document_model.document_id,
                "version_id": version.version_id,
                "version_number": version.version_number,
                "chunk_count": len(chunks),
            }

        except Exception as exc:
            self.db.rollback()

            failed_version = (
                self.version_repository.get_by_id(
                    version.version_id
                )
            )

            if failed_version is not None:
                failed_version.ingestion_status = "FAILED"
                failed_version.ingestion_error = str(exc)
                self.db.commit()

            raise

    def ingest_content(
        self,
        *,
        document_id: int,
        content: str,
        actor_user_id: int | None = None,
    ) -> dict:
        document_model = self.document_repository.get_by_id(document_id)
        if document_model is None:
            raise NotFoundError("Knowledge document not found.")

        if document_model.status != "ACTIVE":
            raise ValidationError(
                f"Cannot ingest into knowledge document with status '{document_model.status}'."
            )

        if not content.strip():
            raise ValidationError("Document content cannot be empty.")

        doc_id_str = create_document_id(
            source_type=document_model.source_type,
            source_name=document_model.source_name,
        )
        domain_doc = KnowledgeDocument(
            document_id=doc_id_str,
            source_type=document_model.source_type,
            source_name=document_model.source_name,
            title=document_model.title,
            content=content,
        )
        domain_doc = self.normalizer.normalize(domain_doc)
        content_hash = create_content_hash(domain_doc.content)
        domain_doc = domain_doc.model_copy(
            update={
                "content_hash": content_hash,
            }
        )

        latest = self.version_repository.get_latest(
            document_model.document_id
        )

        if (
            latest is not None
            and latest.content_hash == domain_doc.content_hash
        ):
            if latest.ingestion_status == "COMPLETED":
                return {
                    "status": "UNCHANGED",
                    "document_id": document_model.document_id,
                    "version_id": latest.version_id,
                    "version_number": latest.version_number,
                    "chunk_count": latest.chunk_count,
                }
            version = latest
        else:
            version = self._create_version(
                document_model=document_model,
                document=domain_doc,
                actor_user_id=actor_user_id,
            )

        version.ingestion_status = "PROCESSING"
        self.db.commit()

        try:
            chunks = self.chunker.chunk(
                domain_doc,
                version_number=version.version_number,
            )

            version.chunk_count = len(chunks)
            version.embedding_model = self._embedding_model_name()
            version.embedding_dimensions = self._embedding_dimensions()
            self.db.commit()

            self.vector_store.add_chunks(chunks)

            version.ingestion_status = "COMPLETED"
            document_model.current_version_id = version.version_id
            self.db.commit()

            if (
                latest is not None
                and latest.version_number != version.version_number
            ):
                try:
                    self.vector_store.delete_document_version(
                        domain_doc.document_id,
                        latest.version_number,
                    )
                except Exception:
                    pass

            return {
                "status": "INGESTED",
                "document_id": document_model.document_id,
                "version_id": version.version_id,
                "version_number": version.version_number,
                "chunk_count": len(chunks),
            }

        except Exception as exc:
            self.db.rollback()

            failed_version = self.version_repository.get_by_id(
                version.version_id
            )

            if failed_version is not None:
                failed_version.ingestion_status = "FAILED"
                failed_version.ingestion_error = str(exc)
                self.db.commit()

            raise

    def _embedding_model_name(self) -> str:
        provider = getattr(self.vector_store, "embedding_provider", None)
        if provider is not None and hasattr(provider, "model_name"):
            return str(provider.model_name)
        return "unknown"

    def _embedding_dimensions(self) -> int:
        provider = getattr(self.vector_store, "embedding_provider", None)
        if provider is not None and hasattr(provider, "dimension"):
            return int(provider.dimension)
        return 1536
