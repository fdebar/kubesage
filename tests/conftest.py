from collections.abc import Generator

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from kubesage.ai.providers import openai_compatible
from kubesage.services import kubernetes_service, loki_service


@pytest.fixture
def span_exporter(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[InMemorySpanExporter]:
    exporter = InMemorySpanExporter()

    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    tracer = provider.get_tracer(openai_compatible.__name__)
    monkeypatch.setattr(openai_compatible, "tracer", tracer)

    loki_tracer = provider.get_tracer(loki_service.__name__)
    monkeypatch.setattr(loki_service, "tracer", loki_tracer)

    kubernetes_tracer = provider.get_tracer(kubernetes_service.__name__)
    monkeypatch.setattr(kubernetes_service, "tracer", kubernetes_tracer)

    yield exporter

    provider.shutdown()
