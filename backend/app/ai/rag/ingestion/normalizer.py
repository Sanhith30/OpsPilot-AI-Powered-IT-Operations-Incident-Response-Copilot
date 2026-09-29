import re

from app.ai.rag.schemas import KnowledgeDocument


class KnowledgeDocumentNormalizer:

    def normalize(
        self,
        document: KnowledgeDocument,
    ) -> KnowledgeDocument:
        content = document.content

        # Normalize line endings.
        content = content.replace(
            "\r\n",
            "\n",
        ).replace(
            "\r",
            "\n",
        )

        # Remove trailing whitespace.
        lines = [
            line.rstrip() for line in content.split("\n")
        ]
        content = "\n".join(lines)

        # Collapse excessive blank lines.
        content = re.sub(
            r"\n{3,}",
            "\n\n",
            content,
        )

        # Remove leading/trailing whitespace.
        content = content.strip()

        if not content:
            raise ValueError(
                "Knowledge document is empty after normalization"
            )

        return document.model_copy(
            update={
                "content": content,
            }
        )
