import requests
from config import settings


class PrometheusService:

    def __init__(self):
        self.base_url = settings.prometheus_url

    def query(self, promql: str):
        response = requests.get(
            f"{self.base_url}/api/v1/query",
            params={
                "query": promql,
            },
            timeout=settings.prometheus_timeout,
        )

        response.raise_for_status()
        data = response.json()

        return data["data"]["result"]

    def cpu_usage(self, namespace, pod):
        query = f"""
            rate(
                container_cpu_usage_seconds_total{{
                namespace="{namespace}",
                pod="{pod}"
                }}[5m]
            )
        """

        result = self.query(query)
        if not result:
            return None

        return float(result[0]["value"][1])

    def memory_usage(self, namespace, pod):

        query = f"""
            container_memory_working_set_bytes{{
            namespace="{namespace}",
            pod="{pod}"
            }}
        """

        result = self.query(query)
        if not result:
            return None

        return int(result[0]["value"][1])

    def restart_count(self, namespace, pod):

        query = f"""
            kube_pod_container_status_restarts_total{{
                namespace="{namespace}",
                pod="{pod}"
            }}
        """

        result = self.query(query)
        if not result:
            return None

        return int(float(result[0]["value"][1]))
