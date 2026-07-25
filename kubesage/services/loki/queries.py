def pod_logs(
    namespace: str,
    pod: str,
) -> str:
    return f'{{namespace="{namespace}",pod="{pod}"}}'


def pod_errors(namespace: str, pod: str) -> None:
    return None


def container_logs(namespace: str, pod: str, logs: str) -> None:
    return None
