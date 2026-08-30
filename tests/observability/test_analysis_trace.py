from collections.abc import Generator
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from kubesage.ai.providers.openai_compatible import OpenAICompatibleProvider
from kubesage.models.ai_report import AIReport
from kubesage.models.analysis import AnalysisTrigger
from kubesage.models.incident import Incident
from kubesage.services.analysis_service import AnalysisService
from kubesage.services.incident_service import IncidentService
from kubesage.services.prometheus_service import PrometheusService

TRACE_MODULES = (
    "kubesage.services.analysis_service",
    "kubesage.services.incident_service",
    "kubesage.analyzers.engine",
    "kubesage.ai.providers.openai_compatible",
    "kubesage.repositories.analysis_repository",
    "kubesage.services.prometheus_service",
)


@pytest.fixture
def span_exporter(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[InMemorySpanExporter]:
    exporter = InMemorySpanExporter()

    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    for module_name in TRACE_MODULES:
        module = __import__(module_name, fromlist=["tracer"])
        monkeypatch.setattr(
            module,
            "tracer",
            provider.get_tracer(module_name),
        )

    yield exporter

    provider.shutdown()


@pytest.fixture
def incident_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def repository() -> MagicMock:
    return MagicMock()


@pytest.fixture
def analysis_service(
    incident_service: MagicMock, repository: MagicMock
) -> AnalysisService:
    return AnalysisService(incident_service, repository)


def get_span(exporter: InMemorySpanExporter, name: str) -> ReadableSpan:
    spans = [span for span in exporter.get_finished_spans() if span.name == name]

    assert len(spans) == 1, (
        f"Expected exactly one span named {name!r}, found {len(spans)}"
    )

    return spans[0]


def get_spans(exporter: InMemorySpanExporter, prefix: str) -> list[ReadableSpan]:
    return [
        span for span in exporter.get_finished_spans() if span.name.startswith(prefix)
    ]


def assert_child_of(child: ReadableSpan, parent: ReadableSpan) -> None:
    assert child.parent is not None
    assert child.parent.span_id == parent.context.span_id
    assert child.context.trace_id == parent.context.trace_id


def test_analysis_creates_execute_span(
    analysis_service: AnalysisService,
    incident_service: MagicMock,
    span_exporter: InMemorySpanExporter,
) -> None:
    incident_service.analyze.return_value = MagicMock()
    analysis_service.analyze("default", "my-pod", AnalysisTrigger.API)
    span = get_span(span_exporter, "analysis.execute")

    assert span.end_time is not None


def test_analysis_execute_contains_expected_attributes(
    analysis_service: AnalysisService,
    incident_service: MagicMock,
    span_exporter: InMemorySpanExporter,
) -> None:
    incident_service.analyze.return_value = MagicMock()
    analysis_service.analyze("production", "api-123", AnalysisTrigger.API)
    span = get_span(span_exporter, "analysis.execute")

    assert span.attributes is not None
    assert span.attributes["analysis.trigger"] == "api"
    assert span.attributes["k8s.namespace"] == "production"
    assert span.attributes["k8s.pod.name"] == "api-123"


def test_analysis_execute_is_root_without_existing_context(
    analysis_service: AnalysisService,
    incident_service: MagicMock,
    span_exporter: InMemorySpanExporter,
) -> None:
    incident_service.analyze.return_value = MagicMock()
    analysis_service.analyze("default", "my-pod", AnalysisTrigger.API)
    span = get_span(span_exporter, "analysis.execute")

    assert span.parent is None


def test_analysis_execute_preserves_existing_parent_context(
    analysis_service: AnalysisService,
    incident_service: MagicMock,
    span_exporter: InMemorySpanExporter,
) -> None:
    incident_service.analyze.return_value = MagicMock()
    test_tracer = trace.get_tracer("test")

    with test_tracer.start_as_current_span("http.request") as parent:
        analysis_service.analyze("default", "my-pod", AnalysisTrigger.API)

        parent_span_id = parent.get_span_context().span_id
        parent_trace_id = parent.get_span_context().trace_id

    execute_span = get_span(span_exporter, "analysis.execute")

    assert execute_span.parent is not None
    assert execute_span.parent.span_id == parent_span_id
    assert execute_span.context.trace_id == parent_trace_id


def test_analysis_execute_success_has_no_error_status(
    analysis_service: AnalysisService,
    incident_service: MagicMock,
    span_exporter: InMemorySpanExporter,
) -> None:
    incident_service.analyze.return_value = MagicMock()
    analysis_service.analyze("default", "my-pod", AnalysisTrigger.API)
    span = get_span(span_exporter, "analysis.execute")

    assert span.status.status_code == trace.StatusCode.UNSET
    assert not any(event.name == "exception" for event in span.events)


def test_analysis_execute_records_error(
    analysis_service: AnalysisService,
    incident_service: MagicMock,
    span_exporter: InMemorySpanExporter,
) -> None:
    incident_service.analyze.side_effect = RuntimeError("Analysis failed")

    with pytest.raises(RuntimeError, match="Analysis failed"):
        analysis_service.analyze("default", "my-pod", AnalysisTrigger.API)

    span = get_span(span_exporter, "analysis.execute")
    assert span.status.status_code == trace.StatusCode.ERROR

    exception_events = [event for event in span.events if event.name == "exception"]
    assert exception_events
    assert any(
        event.attributes is not None
        and event.attributes.get("exception.type") == "RuntimeError"
        and event.attributes.get("exception.message") == "Analysis failed"
        for event in exception_events
    )


def test_incident_build_is_child_of_analysis_execute(
    analysis_service: AnalysisService,
    span_exporter: InMemorySpanExporter,
) -> None:
    incident = MagicMock(spec=Incident)
    incident.containers = []
    incident.events = []
    incident.pod_uid = None
    incident.loki_logs = None

    builder = MagicMock()
    builder.collect.return_value = incident

    incident_service = IncidentService(
        kubernetes=MagicMock(),
        prometheus=MagicMock(),
        metrics=MagicMock(),
        loki=MagicMock(),
        ai=MagicMock(),
        engine=MagicMock(),
        ai_context_builder=MagicMock(),
        prompt_builder=MagicMock(),
        container_snapshot_builder=MagicMock(),
    )

    analysis_service.incident_service = incident_service

    with patch(
        "kubesage.services.incident_service.IncidentBuilder",
        return_value=builder,
    ):
        analysis_service.analyze("default", "my-pod", AnalysisTrigger.API)

    execute_span = get_span(span_exporter, "analysis.execute")
    incident_span = get_span(span_exporter, "analysis.incident.build")

    assert_child_of(incident_span, execute_span)


def test_llm_generate_report_is_child_of_current_analysis_context(
    span_exporter: InMemorySpanExporter,
) -> None:
    response = SimpleNamespace(
        usage=SimpleNamespace(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
        ),
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    parsed=AIReport(
                        summary="Analysis completed",
                    )
                )
            )
        ],
    )

    client = MagicMock()
    client.chat.completions.parse.return_value = response

    provider = OpenAICompatibleProvider(client=client, model="test-model")
    tracer = trace.get_tracer("test.analysis")

    with tracer.start_as_current_span("analysis.ai.analyze") as parent:
        provider.analyze("test prompt")

        parent_span_id = parent.get_span_context().span_id
        parent_trace_id = parent.get_span_context().trace_id

    llm_span = get_span(span_exporter, "llm.generate_report")
    assert llm_span.parent is not None
    assert llm_span.parent.span_id == parent_span_id
    assert llm_span.context.trace_id == parent_trace_id

    assert llm_span.attributes is not None
    assert llm_span.attributes["llm.model"] == "test-model"
    assert llm_span.attributes["llm.tokens.input"] == 10
    assert llm_span.attributes["llm.tokens.output"] == 5
    assert llm_span.attributes["llm.tokens.total"] == 15


def test_llm_generate_report_records_error(
    span_exporter: InMemorySpanExporter,
) -> None:
    client = MagicMock()
    client.chat.completions.parse.side_effect = RuntimeError("LLM unavailable")
    provider = OpenAICompatibleProvider(client=client, model="test-model")

    report = provider.analyze("test prompt")
    assert report.summary == "AI analysis could not be completed."

    span = get_span(span_exporter, "llm.generate_report")
    assert span.status.status_code == trace.StatusCode.ERROR
    assert any(event.name == "exception" for event in span.events)


def test_prometheus_parallel_queries_preserve_parent_context(
    span_exporter: InMemorySpanExporter,
) -> None:
    service = PrometheusService()

    with patch.object(service, "query", return_value=[]):
        service.collect("default", "my-pod")

    collect_span = get_span(span_exporter, "prometheus.collect")
    query_spans = get_spans(span_exporter, "prometheus.query.")

    assert len(query_spans) == 9

    for query_span in query_spans:
        assert_child_of(query_span, collect_span)


def test_prometheus_parallel_queries_have_expected_attributes(
    span_exporter: InMemorySpanExporter,
) -> None:
    service = PrometheusService()

    with patch.object(service, "query", return_value=[]):
        service.collect("production", "api-123")

    query_spans = get_spans(span_exporter, "prometheus.query.")
    assert len(query_spans) == 9

    expected_names = {
        "cpu",
        "memory",
        "container_cpu",
        "container_memory",
        "cpu_throttling",
        "restarts",
        "network_rx",
        "network_tx",
        "filesystem",
    }

    actual_names: set[str] = set()

    for query_span in query_spans:
        assert query_span.attributes is not None

        query_name = query_span.attributes["prometheus.query.name"]

        assert isinstance(query_name, str)

        actual_names.add(query_name)

        assert query_span.attributes["prometheus.query.result_count"] == 0

    assert actual_names == expected_names


def test_analysis_execute_trace_id_is_shared_with_real_incident_service(
    analysis_service: AnalysisService,
    span_exporter: InMemorySpanExporter,
) -> None:
    incident = MagicMock(spec=Incident)
    incident.containers = []
    incident.events = []
    incident.pod_uid = None
    incident.loki_logs = None

    builder = MagicMock()
    builder.collect.return_value = incident

    incident_service = IncidentService(
        kubernetes=MagicMock(),
        prometheus=MagicMock(),
        metrics=MagicMock(),
        loki=MagicMock(),
        ai=MagicMock(),
        engine=MagicMock(),
        ai_context_builder=MagicMock(),
        prompt_builder=MagicMock(),
        container_snapshot_builder=MagicMock(),
    )

    analysis_service.incident_service = incident_service

    with patch(
        "kubesage.services.incident_service.IncidentBuilder",
        return_value=builder,
    ):
        analysis_service.analyze("default", "my-pod", AnalysisTrigger.API)

    execute_span = get_span(span_exporter, "analysis.execute")
    incident_span = get_span(span_exporter, "analysis.incident.build")

    assert incident_span.context.trace_id == execute_span.context.trace_id
    assert_child_of(incident_span, execute_span)
