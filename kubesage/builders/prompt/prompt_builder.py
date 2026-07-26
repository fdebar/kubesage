from kubesage.models.ai_context import AIContext


class PromptBuilder:
    def build(self, context: AIContext) -> str:
        lines: list[str] = []

        lines.append("# Kubernetes Incident")
        lines.append(f"Namespace: {context.incident.namespace}")
        lines.append(f"Pod: {context.incident.pod}")
        lines.append(f"Phase: {context.incident.phase}")
        lines.append("")

        if context.findings:
            lines.append("# Findings")
            for finding in context.findings:
                lines.append(f"- [{finding.severity.value.upper()}] {finding.title}")
                lines.append(f"  Description: {finding.description}")

                if finding.evidences:
                    lines.append("  Evidences:")
                    for evidence in finding.evidences:
                        lines.append(f"    - {evidence}")

                if finding.recommendations:
                    lines.append("  Suggested actions:")
                    for recommendation in finding.recommendations:
                        lines.append(f"    - {recommendation}")

                lines.append("")

        if context.incident.events:
            lines.append("# Kubernetes Events")
            for event in context.incident.events:
                lines.append(f"- [{event.type}] {event.reason}: {event.message}")

            lines.append("")

        if context.incident.logs:
            lines.append("# Logs")
            lines.append(context.incident.logs)
            lines.append("")

        lines.append(
            """
You are a Senior Kubernetes Site Reliability Engineer.

Analyse this incident.

Your objectives are:

1. Identify the most probable root cause.
2. Explain why the issue occurred.
3. Correlate the findings with events and logs.
4. Ignore findings if the evidence contradicts them.
5. Prioritize the suggested actions.
6. Suggest additional investigations if required.
7. Answer using JSON with the following format: 
{
    "summary": "<summary>",
    "root_cause": "<root_cause>",
    "evidence": [<evidence1>, <evidence2>, ...],
    "additional_investigations": [<investigation1>, <investigation2>, ...] 
}
"""
        )

        return "\n".join(lines)
