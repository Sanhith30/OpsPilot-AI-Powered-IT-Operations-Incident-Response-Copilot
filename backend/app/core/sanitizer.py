from __future__ import annotations

import re
from typing import Any

# Patterns matching sensitive secrets in log messages or errors
SENSITIVE_PATTERNS = [
    (re.compile(r"password=([^\s&]+)", re.IGNORECASE), "password=[REDACTED]"),
    (re.compile(r"Bearer\s+([A-Za-z0-9\-_\.]+)", re.IGNORECASE), "Bearer [REDACTED]"),
    (re.compile(r"postgresql(?:\+psycopg2)?://[^:]+:([^@]+)@", re.IGNORECASE), "postgresql://***:***@"),
    (re.compile(r"api[-_]?key[:=]\s*([^\s,]+)", re.IGNORECASE), "api_key=[REDACTED]"),
    (re.compile(r"secret[-_]?key[:=]\s*([^\s,]+)", re.IGNORECASE), "secret_key=[REDACTED]"),
]

# Patterns characteristic of LLM prompt injection attacks
PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
    re.compile(r"system\s+(prompt\s+)?override", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(in\s+)?developer\s+mode", re.IGNORECASE),
    re.compile(r"reveal\s+(the\s+)?(system\s+prompt|passwords|secret\s+keys)", re.IGNORECASE),
    re.compile(r"disregard\s+(the\s+)?rules", re.IGNORECASE),
    re.compile(r"</?system>", re.IGNORECASE),
    re.compile(r"</?prompt>", re.IGNORECASE),
]


def redact_sensitive_data(text: str) -> str:
    """
    Redacts sensitive credentials, passwords, and tokens from error messages or logs.
    """
    if not isinstance(text, str):
        return text

    sanitized = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def detect_prompt_injection(text: str) -> bool:
    """
    Returns True if malicious prompt injection patterns are detected.
    """
    if not isinstance(text, str):
        return False

    for pattern in PROMPT_INJECTION_PATTERNS:
        if pattern.search(text):
            return True
    return False


def sanitize_operational_input(text: str) -> str:
    """
    Neutralizes XML breakout tags and escapes delimiters in untrusted user/incident text.
    """
    if not isinstance(text, str):
        return text

    cleaned = text
    # Neutralize XML tags that match prompt section boundaries
    cleaned = re.sub(r"</?(?:incident|events|deployments|findings|knowledge_evidence|system)>", "", cleaned, flags=re.IGNORECASE)
    return cleaned
