from prometheus_client import Counter
from prometheus_client import Histogram

REQUEST_COUNT = Counter(
    "kubesage_http_requests_total",
    "Total number of HTTP requests",
    [
        "method",
        "endpoint",
        "status_code",
    ],
)

REQUEST_DURATION = Histogram(
    "kubesage_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["endpoint"],
)

ANALYSIS_TOTAL = Counter(
    "kubesage_analysis_total",
    "Number of Kubernetes analyses performed",
    ["status"],
)

ANALYSIS_DURATION = Histogram(
    "kubesage_analysis_duration_seconds",
    "Time spent analyzing incidents",
)

KUBERNETES_ERRORS = Counter(
    "kubesage_kubernetes_errors_total",
    "Kubernetes API errors",
)
