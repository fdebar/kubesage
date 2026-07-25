import structlog

from kubesage.models.incident import Incident

logger = structlog.get_logger()


class MetricsBuilder:
    def build(self, incident: Incident) -> str:
        if incident.prometheus is None:
            logger.warning(
                "prometheus_no_metrics_from_server",
                namespace=incident.namespace,
                pod=incident.pod,
            )
            return "No metrics."

        metrics = []
        usage = incident.prometheus

        if usage.cpu:
            metrics.append(f"CPU: {usage.cpu.value:.3f}")

        if usage.memory:
            metrics.append(f"Memory: {usage.memory.value / 1024 / 1024:.0f} MiB")

        if usage.restarts:
            metrics.append(f"Restarts: {usage.restarts.value:.0f}")

        return "\n".join(metrics)
