from kubesage.builders.prompt.prompt_builder import PromptBuilder
from kubesage.models.ai_context import AIContext
from kubesage.models.incident import Incident


def test_prompt_builder_is_deterministic() -> None:
    incident = Incident(
        namespace="default",
        pod="test-pod",
        phase="Running",
        containers=[],
        events=[],
        kubernetes_logs=None,
        loki_logs=None,
        prometheus=None,
        metrics=None,
    )

    context = AIContext(
        incident=incident,
        findings=[],
    )
    builder = PromptBuilder()

    prompt_1 = builder.build(context)
    prompt_2 = builder.build(context)

    assert prompt_1 == prompt_2
    assert "# Diagnostic Summary" not in prompt_1
