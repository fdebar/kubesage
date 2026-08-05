from kubesage.services.prometheus.queries import build_query


def test_build_query_escapes_labels() -> None:
    query = """
    metric_name{{
        namespace="{namespace}",
        pod="{pod}"
    }}
    """

    result = build_query(query, namespace='prod"namespace', pod="my-pod")

    assert 'namespace="prod\\"namespace"' in result
    assert 'pod="my-pod"' in result
