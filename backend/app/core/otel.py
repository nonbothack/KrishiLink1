from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from app.core.config import settings

_tracer_provider = None


def init_otel(app=None):
    global _tracer_provider

    resource = Resource(
        attributes={
            SERVICE_NAME: "krishilink-api",
            "environment": settings.env,
        }
    )

    _tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(_tracer_provider)

    import os
    import sys

    # Skip console exporter during pytest runs to avoid writing to closed stdout at exit
    if "pytest" in sys.modules or os.environ.get("PYTEST_CURRENT_TEST"):
        pass
    elif settings.env == "production":
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

            otlp_exporter = OTLPSpanExporter(endpoint="http://jaeger:4317", insecure=True)
            _tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        except Exception:
            # Fallback to console
            _tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    else:
        # Console for local dev
        _tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    # Auto-instrument
    if app:
        FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument()
    RedisInstrumentor().instrument()

    return trace.get_tracer(__name__)


def get_tracer(name: str):
    return trace.get_tracer(name)
