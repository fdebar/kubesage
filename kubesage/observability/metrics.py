from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "kubesage_http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
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
    ["reason"],
)

KUBERNETES_DURATION = Histogram(
    "kubesage_kubernetes_duration_seconds",
    "Kubernetes API duration",
)

PROMETHEUS_DURATION = Histogram(
    "kubesage_prometheus_duration_seconds",
    "Prometheus query duration",
)

LLM_REQUESTS = Counter(
    "kubesage_llm_requests_total",
    "Number of LLM requests",
    ["status"],
)

LLM_TOKENS = Histogram("kubesage_llm_tokens", "Number of tokens sent to the LLM")

LLM_DURATION = Histogram("kubesage_llm_duration_seconds", "LLM request duration")

WATCHER_EVENTS_TOTAL = Counter(
    "kubesage_watcher_events_total",
    "Total number of Kubernetes watch events received",
    ["event_type"],
)

WATCHER_INCIDENTS_DETECTED_TOTAL = Counter(
    "kubesage_watcher_incidents_detected_total",
    "Total number of incidents detected by watcher",
    ["reason"],
)

WATCHER_INCIDENTS_IGNORED_TOTAL = Counter(
    "kubesage_watcher_incidents_ignored_total",
    "Total number of duplicate incidents ignored",
    ["reason"],
)

WATCHER_ERRORS_TOTAL = Counter(
    "kubesage_watcher_errors_total", "Total number of watcher errors"
)
