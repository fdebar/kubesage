CPU_QUERY = """
rate(
    container_cpu_usage_seconds_total{
        namespace="%s",
        pod="%s"
    }[5m]
)
"""

MEMORY_QUERY = """
container_memory_working_set_bytes{
    namespace="%s",
    pod="%s"
}
"""

RESTART_QUERY = """
kube_pod_container_status_restarts_total{
    namespace="%s",
    pod="%s"
}
"""

NETWORK_RX_QUERY = """
rate(
    container_network_receive_bytes_total{
        namespace="%s",
        pod="%s"
    }[5m]
)
"""

NETWORK_TX_QUERY = """
rate(
    container_network_transmit_bytes_total{
        namespace="%s",
        pod="%s"
    }[5m]
)
"""

FILESYSTEM_USAGE_QUERY = """
container_fs_usage_bytes{
    namespace="%s",
    pod="%s"
}
"""
