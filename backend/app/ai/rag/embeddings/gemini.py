from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Sequence

from google import genai
from google.genai import types

from app.ai.rag.embeddings.base import EmbeddingProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

_GLOBAL_QUERY_CACHE: dict[str, list[float]] = {}


def _get_cache_file_path() -> Path:
    backend_dir = Path(__file__).resolve().parent.parent.parent.parent
    if backend_dir.name == "app":
        backend_dir = backend_dir.parent
    return backend_dir / ".cache" / "gemini_query_embeddings.json"


def _load_query_cache() -> dict[str, list[float]]:
    global _GLOBAL_QUERY_CACHE
    if _GLOBAL_QUERY_CACHE:
        return _GLOBAL_QUERY_CACHE
    cache_path = _get_cache_file_path()
    if cache_path.exists():
        try:
            with cache_path.open("r", encoding="utf-8") as f:
                _GLOBAL_QUERY_CACHE = json.load(f)
        except Exception:
            pass
    return _GLOBAL_QUERY_CACHE


def _persist_query_cache() -> None:
    cache_path = _get_cache_file_path()
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with cache_path.open("w", encoding="utf-8") as f:
            json.dump(_GLOBAL_QUERY_CACHE, f)
    except Exception:
        pass


class GeminiEmbeddingProvider(EmbeddingProvider):

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        dimension: int,
    ) -> None:
        if not api_key:
            raise ValueError("Gemini API key is required")
        if dimension <= 0:
            raise ValueError("Embedding dimension must be positive")

        self._model = model
        self._dimension = dimension
        self._client = genai.Client(
            api_key=api_key,
        )
        _load_query_cache()

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        if not texts:
            return []

        # Try batch embed_content first
        try:
            batch_result = self._client.models.embed_content(
                model=self._model,
                contents=texts,
                config=types.EmbedContentConfig(
                    output_dimensionality=self._dimension,
                ),
            )
            if batch_result.embeddings and len(batch_result.embeddings) == len(texts):
                return [list(e.values) for e in batch_result.embeddings]
        except Exception:
            pass

        # Fallback to per-document embedding if batch returned fewer embeddings or failed
        embeddings: list[list[float]] = []
        for text in texts:
            if not text.strip():
                embeddings.append([0.0] * self._dimension)
                continue

            last_exc = None
            for attempt in range(5):
                try:
                    result = self._client.models.embed_content(
                        model=self._model,
                        contents=text,
                        config=types.EmbedContentConfig(
                            output_dimensionality=self._dimension,
                        ),
                    )
                    if not result.embeddings:
                        raise RuntimeError("Gemini returned no embedding for document")
                    embeddings.append(list(result.embeddings[0].values))
                    break
                except Exception as exc:
                    last_exc = exc
                    err_str = str(exc)
                    if attempt < 4:
                        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                            m = re.search(r"retry in (\d+)", err_str) or re.search(r"retryDelay': '(\d+)", err_str)
                            delay = float(m.group(1)) + 2.0 if m else 30.0
                            time.sleep(delay)
                        else:
                            time.sleep(2.0 * (attempt + 1))
            else:
                raise last_exc or RuntimeError("Failed to embed document after retries")

        if len(embeddings) != len(texts):
            raise RuntimeError(
                "Embedding count does not match input document count"
            )

        return embeddings

    def embed_query(
        self,
        text: str,
    ) -> list[float]:
        if not text.strip():
            raise ValueError("Query text cannot be empty")

        cache = _load_query_cache()
        if text in cache:
            return cache[text]

        last_exc = None
        for attempt in range(6):
            try:
                result = self._client.models.embed_content(
                    model=self._model,
                    contents=text,
                    config=types.EmbedContentConfig(
                        output_dimensionality=self._dimension,
                    ),
                )
                if not result.embeddings:
                    raise RuntimeError("Gemini returned no embedding")
                res = list(result.embeddings[0].values)
                _GLOBAL_QUERY_CACHE[text] = res
                _persist_query_cache()
                return res
            except Exception as exc:
                last_exc = exc
                err_str = str(exc)
                if attempt < 5:
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        m = re.search(r"retry in (\d+)", err_str) or re.search(r"retryDelay': '(\d+)", err_str)
                        delay = float(m.group(1)) + 2.0 if m else 30.0
                        logger.warning("Gemini 429 quota pause: sleeping %.1f seconds...", delay)
                        time.sleep(delay)
                    else:
                        time.sleep(2.0 * (attempt + 1))

        raise last_exc or RuntimeError("Failed to embed query after retries")
