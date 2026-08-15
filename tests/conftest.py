from collections.abc import Generator

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from kubesage.ai.providers import openai_compatible


@pytest.fixture
def span_exporter(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[InMemorySpanExporter]:
    exporter = InMemorySpanExporter()

    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer(openai_compatible.__name__)
    monkeypatch.setattr(openai_compatible, "tracer", tracer)

    yield exporter

    provider.shutdown()
