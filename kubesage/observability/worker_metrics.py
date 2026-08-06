import structlog
from prometheus_client import start_http_server

from kubesage.utils.config import settings

logger = structlog.get_logger(__name__)


def start_metrics_server(port: int = settings.metrics_port) -> None:
    """
    Starts the Prometheus metrics server on the given port.
    Metrics are exposed for monitoring and alerting purposes.

    Args:
        port: The port on which to start the metrics server.
              Defaults to settings.metrics_port.

    Raises:
        Exception: If the Prometheus metrics server fails to start.
    """

    try:
        start_http_server(port)
        logger.info("prometheus_server_started", port=port)
    except Exception:
        logger.exception("prometheus_server_start_failed")
        raise
