class KubeSageError(Exception):
    """Base exception for KubeSage."""


class DatabaseAvailabilityError(KubeSageError):
    """Database is not available."""


class KubernetesConnectionError(KubeSageError):
    """Cannot communicate with Kubernetes."""


class PodNotFoundError(KubeSageError):
    """Requested pod does not exist."""


class PodIdentityMismatchError(PodNotFoundError):
    """The pod name now refers to a different pod than the requested UID."""


class PrometheusQueryError(KubeSageError):
    """Prometheus request failed."""


class MetricsServerError(KubeSageError):
    """Metrics Server unavailable."""


class AIAnalysisError(KubeSageError):
    """LLM analysis failed."""
