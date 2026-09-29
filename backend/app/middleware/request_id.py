from __future__ import annotations

import time
from uuid import uuid4

from fastapi import Request

from app.observability.logging import set_request_id
from app.observability.metrics import (
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_TOTAL,
)


async def request_observability_middleware(
    request: Request,
    call_next,
):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    set_request_id(request_id)

    start = time.perf_counter()
    response = None

    try:
        response = await call_next(request)
        return response
    finally:
        duration = time.perf_counter() - start
        path = request.url.path
        method = request.method
        status = (
            response.status_code if response is not None else 500
        )

        HTTP_REQUESTS_TOTAL.labels(
            method=method,
            path=path,
            status=str(status),
        ).inc()

        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=method,
            path=path,
        ).observe(duration)

        if response is not None:
            response.headers["X-Request-ID"] = request_id
