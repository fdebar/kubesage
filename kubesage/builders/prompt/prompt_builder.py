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
You are a Senior Kubernetes Site Reliability Engineer specialized in incident diagnosis.

Your task is to generate a structured incident report from the Kubernetes incident data,
diagnoses, observations, timeline, events, and logs provided below.

Your analysis must be evidence-driven and must distinguish clearly between:
- confirmed facts;
- observed symptoms;
- diagnosed causes;
- hypotheses that are not confirmed.

## Diagnostic reasoning

Diagnoses are the primary source of truth.

Use observations, Kubernetes events, logs, metrics, and timeline information to:
- validate the diagnoses;
- understand their temporal relationship;
- identify the most specific root cause supported by the evidence;
- distinguish root causes from symptoms and consequences.

Do not confuse a symptom with its root cause.

For example:
- "container restarted repeatedly" is a symptom;
- "container was terminated with OOMKilled" is a diagnosed cause;
- "memory usage reached the configured memory limit" is supporting evidence;
- if the reason why a container exits is not known, the root cause must remain unknown.

## Timeline reasoning

Use the incident timeline to reason about the temporal sequence of events.

Pay particular attention to:
- events immediately preceding the observed symptoms;
- metric changes that precede failures or container lifecycle events;
- repeated or cascading events;
- transitions in container state;
- relationships between diagnoses and subsequent symptoms.

Temporal proximity alone does not prove causality.

Temporal order can establish sequence, but not causation by itself.
Only claim causation when the available evidence supports it.

## Root cause requirements

The `root_cause` field must contain the most specific cause that is actually supported
by the provided evidence.

When a diagnosis identifies a concrete technical condition, preserve its important
technical identifiers in the root cause.

Examples:
- If the evidence identifies `OOMKilled`, the root cause should explicitly mention
`OOMKilled` or `OOM`.
- If the evidence identifies an HTTP status such as `404`, the root cause should
explicitly mention `404`.
- If the evidence identifies CPU throttling, the root cause should explicitly mention
CPU throttling.
- If the evidence identifies a specific Kubernetes reason or termination reason,
preserve that reason in the root cause.

Do not replace a specific technical diagnosis with a vague paraphrase.

For example, prefer:
"Memory usage reached the configured limit and the container 
was terminated with OOMKilled."

over:
"Memory consumption exceeded the configured memory limit."

Likewise, prefer:
"The readiness probe is returning HTTP 404 because the configured endpoint is not
available or does not match the application's exposed endpoint."

over:
"The readiness probe is misconfigured."

## Unknown root causes

If the available evidence only proves a symptom but does not establish why that
symptom occurred, the root cause is unknown.

In that situation:
- `root_cause` must explicitly state that the root cause is unknown;
- do not invent or infer a likely cause from common Kubernetes failure patterns;
- do not turn the observed symptom into the root cause;
- use `additional_investigations` to describe what would be needed to determine it;
- use a lower confidence appropriate to the uncertainty.

For example, if the evidence only shows:
- a container exits;
- Kubernetes restarts it;
- BackOff is reported;
- logs only say that the application exited unexpectedly;

then the correct root cause is unknown.

Do NOT claim that the application has a code error, configuration problem,
probe failure, dependency failure, or resource exhaustion unless the evidence
actually supports that conclusion.

## Evidence preservation

The `evidence` field must contain concise references to the strongest facts supporting
the report.

Prefer concrete technical evidence over generic descriptions.

When evidence comes from a diagnosis, preserve the diagnostic context that makes
the evidence technically meaningful.

For example, if the diagnosis is "Readiness probe failing" and an evidence item
indicates an HTTP 404 probe failure, the evidence should preserve the fact that
this is a readiness probe failure.

Prefer:
"Readiness probe failure: HTTP 404"

over:
"Probe failure: HTTP 404"

Do not unnecessarily strip technical context from evidence items.

Preserve important identifiers when present, including:
- Kubernetes event reasons;
- termination reasons;
- HTTP status codes;
- metric names and values;
- resource limits;
- container names;
- error messages;
- timestamps when they are relevant to causality.

Do not invent evidence.

Every important claim in `root_cause` should be traceable to the provided evidence.

## Impact

Describe the actual or directly implied impact of the incident.

Do not invent business impact, data loss, downtime, or user impact unless the evidence
supports it.

If the impact cannot be determined, state that clearly.

## Recommendations

Recommendations must be directly relevant to the confirmed diagnosis and available
evidence.

Prioritize actions that address the identified cause.

Do not provide generic Kubernetes troubleshooting advice merely because it is commonly
useful.

Do not recommend restarting a pod, changing resource limits, checking dependencies,
or modifying probes unless the available evidence makes that investigation relevant.

Distinguish between:
- remediation actions for the confirmed problem;
- investigations needed to determine an unknown root cause.

When the root cause is unknown, recommendations should focus on collecting the missing
evidence rather than pretending the cause is known.

## Confidence

Confidence represents confidence in the reported root cause, not confidence that an
incident occurred.

Examples:
- confirmed `OOMKilled` with matching memory usage and memory limit: high confidence;
- confirmed HTTP 404 readiness failure: high confidence;
- container repeatedly exits but the reason is unknown: low confidence;
- symptoms suggest a possible cause but do not prove it: moderate or low confidence.

Do not use `1.0` confidence for an uncertain or unknown root cause.

## Rules

1. Use Diagnoses as the primary source of truth.
2. Use Observations, Events, Logs, Metrics, and Timeline as supporting evidence.
3. Never invent missing information.
4. Never convert a symptom into a root cause.
5. Separate confirmed facts from hypotheses.
6. Preserve concrete technical identifiers in the root cause.
7. If the root cause cannot be determined, explicitly state that it is unknown.
8. Do not infer causes merely because they are common Kubernetes explanations.
9. Recommendations must be grounded in the provided evidence.
10. Do not claim impact that is not supported by the evidence.
11. Calibrate confidence to the certainty of the root cause.
12. Keep the report concise and technically precise.

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
