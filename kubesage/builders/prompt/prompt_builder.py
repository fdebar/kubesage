from kubesage.models.ai_context import AIContext
from kubesage.models.finding import Finding


class PromptBuilder:
    def build(self, context: AIContext) -> str:
        lines: list[str] = []

        lines.append("# Kubernetes Incident")
        lines.append(f"Namespace: {context.incident.namespace}")
        lines.append(f"Pod: {context.incident.pod}")
        lines.append(f"Phase: {context.incident.phase}")
        lines.append("")

        if context.has_findings:
            lines.append("# Diagnostic Summary")
            lines.append(f"Count: {context.finding_count}")
            if context.highest_severity:
                lines.append(
                    f"Highest Severity: {context.highest_severity.value.upper()}"
                )

            if context.diagnoses:
                lines.append("# Diagnoses")
                for finding in context.diagnoses:
                    self._append_finding(lines, finding)

            if context.observations:
                lines.append("# Observations")
                for finding in context.observations:
                    self._append_finding(lines, finding)

        if context.incident.events:
            lines.append("# Kubernetes Events")
            for event in context.incident.events:
                lines.append(f"- [{event.type}] {event.reason}: {event.message}")
            lines.append("")

        if context.incident.logs:
            lines.append("# Logs")
            lines.append(context.incident.logs)
            lines.append("")

        if context.recommendations:
            lines.append("# Recommendations")

            for recommendation in context.recommendations:
                lines.append(f"- {recommendation}")

            lines.append("")

        lines.append(
            """
You are a Senior Kubernetes Site Reliability Engineer.

Your role is to generate an incident report from the provided analysis.

Rules:

1. Use Diagnoses as the primary source of truth.
2. Use Observations only as supporting signals.
3. Never invent missing information.
4. Do not override confirmed diagnoses.
5. Explain the incident using only provided evidence.
6. Prioritize recommendations based on severity and confidence.
7. Answer using JSON only.
"""
        )
        print("\n".join(lines))
        return "\n".join(lines)

    def _append_finding(self, lines: list[str], finding: Finding) -> None:
        lines.append(f"### {finding.title}")
        lines.append(f"Severity: {finding.severity.value}")
        lines.append(f"Confidence: {finding.confidence:.2f}")
        lines.append(f"Description: {finding.description}")

        if finding.caused_by:
            lines.append("Caused by:")
            for cause in finding.caused_by:
                lines.append(f"    - {cause}")

        if finding.structured_evidences:
            lines.append("Evidence:")
            for evidence in finding.structured_evidences:
                value = evidence.value

                if evidence.unit:
                    value = f"{value}{evidence.unit}"
                lines.append(f"    - {evidence.name}: {value}")

            lines.append("")
