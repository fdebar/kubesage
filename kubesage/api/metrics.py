from prometheus_client import Counter, Histogram

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

KUBERNETES_DURATION = Histogram(
    "kubesage_kubernetes_duration_seconds",
    "Kubernetes API duration",
)

PROMETHEUS_DURATION = Histogram(
    "kubesage_prometheus_duration_seconds",
    "Prometheus query duration",
)

OPENAI_REQUESTS = Counter(
    "kubesage_openai_requests_total",
    "Number of LLM requests",
    [
        "status",
    ],
)

OPENAI_TOKENS = Histogram(
    "kubesage_openai_tokens",
    "Number of tokens sent to the LLM",
)

OPENAI_DURATION = Histogram(
    "kubesage_openai_duration_seconds",
    "LLM request duration",
)
