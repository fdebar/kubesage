from models.ai_context import AIContext
from models.incident import Incident
from models.finding import Finding
from observability import get_logger


class ContextBuilder:
    def build(self, incident: Incident, findings: list[Finding]) -> AIContext:
        logger = get_logger(__name__)
        logger.info("Building AI context...")

        summary = self._build_summary(findings)
        metrics = self._metrics_summary(incident)

        return AIContext(
            incident=incident,
            findings=findings,
            summary=summary,
            metrics_summary=metrics,
        )

    def _build_summary(self, findings: list[Finding]) -> str:
        if not findings:
            return "No issue detected."

        return "\n".join(f"- {f.title}" for f in findings)

    def _metrics_summary(self, incident: Incident) -> str:
        metrics = []

        if incident.prometheus is None:
            return "No metrics."

        usage = incident.prometheus
        if usage.cpu:
            metrics.append(f"CPU: {usage.cpu.value:.3f}")
        if usage.memory:
            metrics.append(f"Memory: {usage.memory.value / 1024 / 1024:.0f} MiB")
        if usage.restarts:
            metrics.append(f"Restarts: {usage.restarts.value:.0f}")

        return "\n".join(metrics)
