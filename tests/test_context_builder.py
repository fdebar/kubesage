from unittest.mock import MagicMock

from kubesage.analyzers.engine import DiagnosticEngine
from kubesage.builders.context_builder import ContextBuilder
from kubesage.builders.prompt_builder import PromptBuilder


def test_summary_contains_findings() -> None:
    builder = ContextBuilder()

    finding1 = MagicMock()
    finding1.title = "High CPU Usage"

    finding2 = MagicMock()
    finding2.title = "OOM Killed"

    incident = MagicMock()
    incident.prometheus = None

    context = builder.build(incident=incident, findings=[finding1, finding2])

    assert "High CPU Usage" in context.summary
    assert "OOM Killed" in context.summary


def test_prompt_contains_logs() -> None:
    builder = PromptBuilder()

    context = MagicMock()
    context.findings = []
    context.incident = MagicMock()
    context.incident.namespace = "default"
    context.incident.pod = "my-pod"
    context.incident.phase = "Running"
    context.incident.events = []
    context.incident.logs = "ERROR: connection refused"
    context.metrics_summary = "No metrics."

    prompt = builder.build(context)

    assert "ERROR: connection refused" in prompt


def test_all_rules_are_loaded() -> None:
    engine = DiagnosticEngine()

    assert len(engine.rules) > 0
    assert hasattr(engine.rules[0], "name")
    assert hasattr(engine.rules[0], "evaluate")
