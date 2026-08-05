CPU_QUERY = """
rate(
    container_cpu_usage_seconds_total{{
        namespace="{namespace}",
        pod="{pod}"
    }}[5m]
)
"""

MEMORY_QUERY = """
container_memory_working_set_bytes{{
    namespace="{namespace}",
    pod="{pod}"
}}
"""

RESTART_QUERY = """
kube_pod_container_status_restarts_total{{
    namespace="{namespace}",
    pod="{pod}"
}}
"""

NETWORK_RX_QUERY = """
rate(
    container_network_receive_bytes_total{{
        namespace="{namespace}",
        pod="{pod}"
    }}[5m]
)
"""

NETWORK_TX_QUERY = """
rate(
    container_network_transmit_bytes_total{{
        namespace="{namespace}",
        pod="{pod}"
    }}[5m]
)
"""

FILESYSTEM_USAGE_QUERY = """
container_fs_usage_bytes{{
    namespace="{namespace}",
    pod="{pod}"
}}
"""

CPU_THROTTLING_QUERY = """
sum by (pod) (
  rate(container_cpu_cfs_throttled_seconds_total{{
    namespace="{namespace}",
    pod="{pod}"
  }}[5m])
)
/
sum by (pod) (
  rate(container_cpu_cfs_periods_total{{
    namespace="{namespace}",
    pod="{pod}"
  }}[5m])
)
"""

CONTAINER_CPU_QUERY = """
sum by (container) (
    rate(
        container_cpu_usage_seconds_total{{
            namespace="{namespace}",
            pod="{pod}",
            container!="POD",
            container!=""
        }}[5m]
    )
)
"""


CONTAINER_MEMORY_QUERY = """
sum by (container) (
    container_memory_usage_bytes{{
        namespace="{namespace}",
        pod="{pod}",
        container!="POD",
        container!=""
    }}
)
"""


def escape_label(value: str) -> str:
    """Escape Prometheus label values."""

    return value.replace("\\", "\\\\").replace('"', '\\"')


def build_query(query: str, **labels: str) -> str:
    """
    Build a PromQL query by replacing placeholders safely.
    """

    escaped_labels = {key: escape_label(value) for key, value in labels.items()}
    try:
        return query.format(**escaped_labels)
    except ValueError as exc:
        raise ValueError(
            "Invalid PromQL template. Escape Prometheus braces with { { and } }."
        ) from exc
