from __future__ import annotations

import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.fastapi import (
    FastAPIInstrumentor,
)
from opentelemetry.instrumentation.sqlalchemy import (
    SQLAlchemyInstrumentor,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import (
    TracerProvider,
)
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
)
from opentelemetry.semconv.resource import (
    ResourceAttributes,
)

_configured = False


def configure_tracing(app, engine=None) -> None:
    global _configured

    if _configured:
        return

    service_name = os.getenv(
        "OTEL_SERVICE_NAME",
        "opspilot-backend",
    )

    resource = Resource.create(
        {
            ResourceAttributes.SERVICE_NAME: service_name,
        }
    )

    provider = TracerProvider(resource=resource)

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    if endpoint:
        insecure = (
            os.getenv(
                "OTEL_EXPORTER_OTLP_INSECURE",
                "true",
            ).lower()
            == "true"
        )

        exporter = OTLPSpanExporter(
            endpoint=endpoint,
            insecure=insecure,
        )

        provider.add_span_processor(
            BatchSpanProcessor(exporter)
        )

    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)

    if engine is not None:
        SQLAlchemyInstrumentor().instrument(
            engine=engine,
        )

    _configured = True


def get_tracer(name: str = "opspilot"):
    return trace.get_tracer(name)
