import structlog

from kubesage.models.incident import Incident

logger = structlog.get_logger()


class MetricsBuilder:
    def build(self, incident: Incident) -> str:
        metrics = []

        if incident.prometheus is None:
            logger.warning(
                "prometheus_no_metrics_from_server",
                namespace=incident.namespace,
                pod=incident.pod,
            )
            return "No metrics."

        usage = incident.prometheus
        if usage.cpu:
            metrics.append(f"CPU: {usage.cpu.value:.3f}")
        if usage.memory:
            metrics.append(f"Memory: {usage.memory.value / 1024 / 1024:.0f} MiB")
        if usage.restarts:
            metrics.append(f"Restarts: {usage.restarts.value:.0f}")
        if usage.filesystem:
            metrics.append(
                f"Filesystem: {usage.filesystem.value / 1024 / 1024 / 1024:.2f} GiB"
            )
        if usage.network_rx:
            metrics.append(f"Network RX: {usage.network_rx.value:.2f} bytes/s")
        if usage.network_tx:
            metrics.append(f"Network TX: {usage.network_tx.value:.2f} bytes/s")
        if usage.request_rate:
            metrics.append(f"Request Rate: {usage.request_rate.value:.2f} req/s")
        if usage.error_rate:
            metrics.append(f"Error Rate: {usage.error_rate.value:.2f} %")
        if usage.latency:
            metrics.append(f"Latency (p95): {usage.latency.value:.2f} ms")

        return "\n".join(metrics)
