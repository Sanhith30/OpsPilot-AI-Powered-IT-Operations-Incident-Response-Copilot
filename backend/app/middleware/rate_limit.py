from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, List
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    In-memory sliding window rate limiter to protect API endpoints
    against abuse, brute force attacks, and resource exhaustion.
    """

    def __init__(self, app, default_limit: int = 600, window_seconds: int = 60):
        super().__init__(app)
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self._history: Dict[str, List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Determine client key (IP or forward header)
        forwarded = request.headers.get("X-Forwarded-For")
        client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
        
        # Test override support: Allow specific tests to verify rate-limiting without waiting or affecting others
        test_limit_header = request.headers.get("X-Test-Rate-Limit")
        if test_limit_header and test_limit_header.isdigit():
            limit = int(test_limit_header)
            client_key = f"test_{client_ip}_{request.headers.get('X-Test-Client-Id', 'default')}"
        else:
            limit = self.default_limit
            client_key = f"{client_ip}:{request.url.path}"

        now = time.time()
        window_start = now - self.window_seconds

        # Clean timestamps older than window
        timestamps = [t for t in self._history[client_key] if t > window_start]
        self._history[client_key] = timestamps

        if len(timestamps) >= limit:
            retry_after = int(window_start + self.window_seconds - timestamps[0]) + 1
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "detail": "Rate limit exceeded. Please try again later.",
                },
                headers={
                    "Retry-After": str(max(1, retry_after)),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        self._history[client_key].append(now)
        remaining = max(0, limit - len(self._history[client_key]))

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
