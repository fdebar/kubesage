from kubesage.utils.config import settings
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
import structlog

logger = structlog.get_logger()


def setup_telemetry(app: FastAPI) -> None:
    """
    Configure OpenTelemetry for FastAPI.
    """

    resource = Resource.create(
        {
            "service.name": settings.app_name,
            "service.version": settings.app_version,
        }
    )

    provider = TracerProvider(resource=resource)
    if settings.otlp_endpoint:
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otlp_endpoint))
        )
        logger.info("opentelemetry_with_otlp_endpoint", endpoint=settings.otlp_endpoint)
    else:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        logger.info("opentelemetry_with_console_exporter")

    trace.set_tracer_provider(provider)

    if isinstance(provider, TracerProvider):
        provider.shutdown()

    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
