import logging
import sys

from kubesage.observability.tracing import current_trace_context


class OpenTelemetryContextFilter(logging.Filter):
    """Inject the current OpenTelemetry context into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        context = current_trace_context()

        record.trace_id = context.trace_id or "-"
        record.span_id = context.span_id or "-"

        return True


def setup_logging() -> None:
    """
    Configure application logging.
    """

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(OpenTelemetryContextFilter())

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s "
        "trace_id=%(trace_id)s span_id=%(span_id)s %(message)s"
    )

    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
