def pod_logs(namespace: str, pod: str) -> str:
    return f'{{namespace="{namespace}", pod="{pod}"}}'


def pod_errors(namespace: str, pod: str) -> str:
    return (
        f'{{namespace="{namespace}", pod="{pod}"}} |~ "(?i)error|exception|fatal|panic"'
    )


def pod_warnings(namespace: str, pod: str) -> str:
    return f'{{namespace="{namespace}", pod="{pod}"}} |~ "(?i)warn|warning"'


def container_logs(namespace: str, pod: str, container: str) -> str:
    return f'{{namespace="{namespace}", pod="{pod}", container="{container}"}}'
