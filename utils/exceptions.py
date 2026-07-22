class KubeSageError(Exception):
    """Base exception for KubeSage."""


class KubernetesConnectionError(KubeSageError):
    """Cannot communicate with Kubernetes."""


class PodNotFoundError(KubeSageError):
    """Requested pod does not exist."""


class PrometheusQueryError(KubeSageError):
    """Prometheus request failed."""


class MetricsServerError(KubeSageError):
    """Metrics Server unavailable."""


class AIAnalysisError(KubeSageError):
    """LLM analysis failed."""
