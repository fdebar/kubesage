from pathlib import Path

from kubesage.models.ai_context import AIContext


class PromptBuilder:
    def __init__(self) -> None:
        template_path = Path(__file__).parent.parent / "prompts" / "sre_analysis.txt"
        self.template = template_path.read_text(encoding="utf-8")

    def build(self, context: AIContext) -> str:
        findings = "\n".join(
            f"- [{f.severity}] {f.title}: {f.description}" for f in context.findings
        )
        events = "\n".join(
            f"- {event.reason}: {event.message}" for event in context.incident.events
        )

        return f"""
{self.template}

========================
INCIDENT
========================

Namespace:
{context.incident.namespace}

Pod:
{context.incident.pod}

Phase:
{context.incident.phase}

========================
FINDINGS
========================

{findings}

========================
METRICS
========================

{context.metrics_summary}

========================
EVENTS
========================

{events}

========================
LOGS
========================

{context.incident.logs}
"""
