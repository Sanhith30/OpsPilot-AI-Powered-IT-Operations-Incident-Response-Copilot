import hashlib


def create_document_id(
    *,
    source_type: str,
    source_name: str,
) -> str:
    payload = (
        f"{source_type.strip().lower()}:"
        f"{source_name.strip().lower()}"
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


def create_content_hash(
    content: str,
) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def create_chunk_id(
    *,
    document_id: str,
    version_number: int,
    chunk_index: int,
    content: str,
) -> str:
    payload = (
        f"{document_id}:"
        f"{version_number}:"
        f"{chunk_index}:"
        f"{content}"
    ).encode("utf-8")

    digest = hashlib.sha256(payload).hexdigest()

    return f"{document_id[:16]}-v{version_number}-{digest[:20]}"
