from unittest.mock import MagicMock

from kubesage.builders.prompt.prompt_builder import PromptBuilder


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
