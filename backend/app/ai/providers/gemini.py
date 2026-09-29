from __future__ import annotations

import logging
import os
import re
import time
from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.ai.providers.base import LLMProvider
from app.ai.providers.config import LLMConfig
from app.observability.metrics import (
    LLM_REQUESTS_TOTAL,
    LLM_REQUEST_DURATION_SECONDS,
)
from app.observability.tracing import get_tracer

tracer = get_tracer("opspilot.llm")
logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """
    Gemini implementation of the provider-independent LLM interface.
    """

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        api_key = (
            config.api_key.get_secret_value()
            if config.api_key is not None
            else os.getenv("GEMINI_API_KEY")
        )
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is required when using the Gemini provider."
            )

        self.api_key = api_key
        self.model = config.model
        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=config.timeout_seconds * 1000
            ),
        )

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        metadata: dict[str, Any] | None = None,
        response_schema: type[BaseModel] | None = None,
    ) -> str:
        """
        Generate a response from Gemini.
        When response_schema is provided, Gemini is instructed to return JSON
        matching that Pydantic schema.
        """
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
        )

        if response_schema is not None:
            config.response_mime_type = "application/json"
            config.response_schema = response_schema

        start = time.perf_counter()
        with tracer.start_as_current_span("llm.generate") as span:
            span.set_attribute(
                "opspilot.llm.provider",
                "gemini",
            )
            span.set_attribute(
                "opspilot.llm.model",
                self.config.model,
            )

            try:
                for attempt in range(5):
                    try:
                        response = self.client.models.generate_content(
                            model=self.config.model,
                            contents=user_prompt,
                            config=config,
                        )
                        break
                    except Exception as exc:
                        exc_str = str(exc)
                        if "perday" in exc_str.lower() or "per_day" in exc_str.lower():
                            raise

                        if (
                            "429" in exc_str
                            or "resource_exhausted" in exc_str.lower()
                            or "quota" in exc_str.lower()
                        ) and attempt < 4:
                            delay = 15.0
                            m = re.search(r"retry in (\d+(\.\d+)?)s", exc_str, re.IGNORECASE) or re.search(
                                r"'retryDelay':\s*'(\d+)s'", exc_str
                            )
                            if m:
                                delay = float(m.group(1)) + 1.0
                            logger.warning(
                                "Gemini 429 rate limit hit. Sleeping %.1fs before attempt %d...",
                                delay,
                                attempt + 1,
                            )
                            time.sleep(delay)
                            continue
                        if "503" in exc_str and attempt < 3:
                            time.sleep(2 * (attempt + 1))
                            continue
                        raise

                text = response.text if response is not None else None
                if not text:
                    raise RuntimeError(
                        "Gemini returned an empty response."
                    )

                duration = time.perf_counter() - start
                LLM_REQUESTS_TOTAL.labels(
                    provider="gemini",
                    model=self.config.model,
                    status="SUCCESS",
                ).inc()
                LLM_REQUEST_DURATION_SECONDS.labels(
                    provider="gemini",
                    model=self.config.model,
                ).observe(duration)
                span.set_attribute(
                    "opspilot.llm.status",
                    "SUCCESS",
                )
                return text

            except Exception as exc:
                duration = time.perf_counter() - start
                LLM_REQUESTS_TOTAL.labels(
                    provider="gemini",
                    model=self.config.model,
                    status="FAILURE",
                ).inc()
                LLM_REQUEST_DURATION_SECONDS.labels(
                    provider="gemini",
                    model=self.config.model,
                ).observe(duration)
                span.record_exception(exc)
                span.set_attribute(
                    "opspilot.llm.status",
                    "FAILURE",
                )
                raise

    def close(self) -> None:
        """Release the underlying client resources."""
        self.client.close()
