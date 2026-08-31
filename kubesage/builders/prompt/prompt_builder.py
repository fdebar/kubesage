from kubesage.models.ai_context import AIContext
from kubesage.models.finding import Finding


class PromptBuilder:
    def build(self, ai: AIContext) -> str:
        lines: list[str] = []

        self._append_incident(lines, ai)
        self._append_timeline(lines, ai)
        self._append_diagnostics(lines, ai)
        self._append_observations(lines, ai)
        self._append_events(lines, ai)
        self._append_logs(lines, ai)
        self._append_recommendations(lines, ai)
        self._append_instructions(lines)
        self._append_summary(lines, ai)

        print("\n".join(lines))

        return "\n".join(lines)

    def _append_incident(self, lines: list[str], ai: AIContext) -> None:
        lines.append("# Kubernetes Incident")
        lines.append(f"Namespace: {ai.ctx.namespace}")
        lines.append(f"Pod: {ai.ctx.pod}")
        lines.append(f"Phase: {ai.ctx.phase}")
        lines.append("")

    def _append_timeline(self, lines: list[str], ai: AIContext) -> None:
        if not ai.ctx.timeline:
            return

        lines.append("# Incident Timeline")
        for event in ai.ctx.timeline:
            line = (
                f"- [{event.timestamp.isoformat()}] "
                f"[{event.severity.value}] "
                f"{event.source.value} | "
                f"{event.title}"
            )

            lines.append(line)
            if event.description:
                lines.append(f"  {event.description}")

        lines.append("")

    def _append_diagnostics(self, lines: list[str], ai: AIContext) -> None:
        if not ai.diagnoses:
            return

        lines.append("# Diagnoses")
        for finding in ai.diagnoses:
            self._append_finding(lines, finding)

    def _append_observations(self, lines: list[str], ai: AIContext) -> None:
        if not ai.observations:
            return

        lines.append("# Observations")
        for finding in ai.observations:
            self._append_finding(lines, finding)

    def _append_events(self, lines: list[str], ai: AIContext) -> None:
        if not ai.ctx.events:
            return

        lines.append("# Kubernetes Events")
        for event in ai.ctx.events:
            lines.append("")
            lines.append(f"- Type: {event.type}")
            lines.append(f"  Reason: {event.reason}")
            lines.append(f"  Message: {event.message}")

            if event.last_timestamp:
                lines.append(f"  Timestamp: {event.last_timestamp.isoformat()}")

        lines.append("")

    def _append_logs(self, lines: list[str], ai: AIContext) -> None:
        if not ai.ctx.logs:
            return

        lines.append("# Logs")
        lines.append(ai.ctx.logs)
        lines.append("")

    def _append_recommendations(self, lines: list[str], ai: AIContext) -> None:
        if not ai.recommendations:
            return

        lines.append("# Recommendations")

        for recommendation in ai.recommendations:
            lines.append(f"- {recommendation}")

        lines.append("")

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
                value = evidence.value or ""
                if evidence.unit:
                    value = f"{value}{evidence.unit}"

                lines.append("")
                lines.append(f"- Type: {evidence.type or 'unknown'}")
                lines.append(f"  Name: {evidence.name}")
                lines.append(f"  Value: {value}")

                if evidence.source:
                    lines.append(f"  Source: {evidence.source}")

                if evidence.description:
                    lines.append(f"  Description: {evidence.description}")

                lines.append("")

    def _append_summary(self, lines: list[str], ai: AIContext) -> None:
        if not ai.has_findings:
            return

        lines.append("# Diagnostic Summary")
        lines.append(f"Count: {ai.finding_count}")

        if ai.highest_severity:
            lines.append(f"Highest Severity: {ai.highest_severity.value.upper()}")

        lines.append("")

    def _append_instructions(self, lines: list[str]) -> None:
        lines.append(
            """
You are a Senior Kubernetes Site Reliability Engineer.

Your role is to generate a structured incident report from the provided analysis.

## Timeline reasoning

Use the incident timeline to reason about the temporal sequence of events.

Pay particular attention to:
- events immediately preceding the observed symptoms;
- metric changes that precede failures or container lifecycle events;
- repeated or cascading events;
- the distinction between symptoms and likely causes.

Temporal proximity alone does not prove causality.
Temporal order can establish sequence, but not causation by itself.
Do not claim that an event caused another event unless the available evidence 
supports that conclusion.

## Your objectives

1. Validate the detected diagnoses.
2. Identify the most likely root cause when supported by the available evidence.
   If the root cause cannot be determined from the available evidence,
   explicitly state that it is unknown rather than guessing.
3. Explain the impact of the incident.
4. Recommend remediation actions supported by the available evidence.
5. Suggest additional investigations if information is missing.

## Rules

1. Use Diagnoses as the primary source of truth.
2. Use Observations only as supporting signals.
3. Never invent missing information.
4. Separate confirmed facts from hypotheses.
5. Base conclusions only on provided evidence.
6. If the evidence is insufficient to determine a root cause,
   state that the root cause is unknown.
7. Do not propose specific causes merely because they are common
   explanations for the observed symptoms.
8. Recommendations must be grounded in the provided evidence.
9. Prioritize recommendations using severity and confidence.

Return JSON matching this schema:

{
  "summary": "...",
  "root_cause": "...",
  "confidence": 0.0,
  "impact": "...",
  "evidence": [],
  "recommendations": [],
  "additional_investigations": []
}
"""
        )
