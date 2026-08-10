import time

import structlog
from kubernetes import client
from kubernetes.client import Configuration, V1Pod
from kubernetes.client.exceptions import ApiException

from kubesage.models.cluster_info import ClusterInfo
from kubesage.models.container import (
    ContainerResources,
    ContainerStatus,
    PodResources,
)
from kubesage.models.event import Event
from kubesage.models.kubernetes_snapshot import KubernetesSnapshot
from kubesage.models.log import LogSnapshot
from kubesage.observability.metrics import KUBERNETES_DURATION, KUBERNETES_ERRORS
from kubesage.providers.kubernetes_provider import KubernetesProvider
from kubesage.utils.config import settings
from kubesage.utils.exceptions import PodNotFoundError
from kubesage.utils.kube_client import create_core_v1_api
from kubesage.utils.resource_quantity import parse_cpu_quantity, parse_memory_quantity

logger = structlog.get_logger()


class KubernetesService(KubernetesProvider):
    """Service for collecting data from Kubernetes."""

    def __init__(self) -> None:
        self.v1 = create_core_v1_api()

    def collect(self, namespace: str, pod: str) -> KubernetesSnapshot:
        start = time.perf_counter()
        logger.info("kubernetes_starting_collecting_data", namespace=namespace, pod=pod)

        try:
            pod_info = self.v1.read_namespaced_pod(name=pod, namespace=namespace)
        except ApiException as exc:
            if exc.status == 404:
                KUBERNETES_ERRORS.labels(reason="Pod Not Found").inc()
                logger.error(
                    "kubernetes_pod_not_found",
                    namespace=namespace,
                    pod=pod,
                    status=exc.status,
                    reason=exc.reason,
                )
                raise PodNotFoundError(
                    f"Pod '{pod}' not found in namespace '{namespace}'."
                ) from None
            KUBERNETES_ERRORS.labels(reason="API Error").inc()
            logger.error(
                "kubernetes_api_error",
                status=exc.status,
                reason=exc.reason,
            )
            return self._empty_snapshot(namespace, pod)
        except Exception as exc:  # noqa: BLE001
            KUBERNETES_ERRORS.labels(reason=str(exc)).inc()
            logger.warning(
                "kubernetes_failed_to_collect_data", namespace=namespace, pod=pod
            )
            return self._empty_snapshot(namespace, pod)

        logs = self._collect_logs(namespace, pod)
        containers = self._collect_containers(pod_info)
        events = self._collect_events(namespace, pod)
        resources = self._collect_resources(pod_info)

        KUBERNETES_DURATION.observe(time.perf_counter() - start)

        return KubernetesSnapshot(
            namespace=namespace,
            pod=pod,
            phase=pod_info.status.phase,
            logs=logs,
            containers=containers,
            events=events,
            resources=resources,
        )

    def _collect_logs(self, namespace: str, pod: str) -> LogSnapshot:
        try:
            logs = self.v1.read_namespaced_pod_log(
                name=pod,
                namespace=namespace,
                tail_lines=settings.log_tail_lines,
            )
        except ApiException as exc:
            if exc.status == 404:
                logger.warning(
                    "kubernetes_failed_to_collect_logs",
                    namespace=namespace,
                    pod=pod,
                    status=exc.status,
                    reason=exc.reason,
                )
            raise PodNotFoundError(
                f"Pod '{pod}' not found in namespace '{namespace}'."
            ) from None
        except Exception:
            logger.warning(
                "kubernetes_failed_to_collect_logs", namespace=namespace, pod=pod
            )
            return LogSnapshot(source="kubernetes", lines=[])

        if isinstance(logs, bytes):
            logs = logs.decode("utf-8")

        return LogSnapshot(
            source="kubernetes",
            lines=logs.split("\n") if logs else [],
        )

    def _collect_containers(self, pod_info: V1Pod) -> list[ContainerStatus]:
        containers = []

        for container in pod_info.status.container_statuses or []:
            waiting_reason = None
            waiting_message = None

            if container.state and container.state.waiting:
                waiting_reason = container.state.waiting.reason
                waiting_message = container.state.waiting.message

            last_exit_code = None
            last_exit_reason = None

            if container.last_state and container.last_state.terminated:
                last_exit_code = container.last_state.terminated.exit_code
                last_exit_reason = container.last_state.terminated.reason

            containers.append(
                ContainerStatus(
                    name=container.name,
                    image=container.image,
                    ready=container.ready,
                    restart_count=container.restart_count,
                    waiting_reason=waiting_reason,
                    waiting_message=waiting_message,
                    last_exit_code=last_exit_code,
                    last_exit_reason=last_exit_reason,
                )
            )

        return containers

    def _collect_events(self, namespace: str, pod: str) -> list[Event]:
        try:
            events = self.v1.list_namespaced_event(
                namespace=namespace,
                field_selector=f"involvedObject.name={pod}",
            )
        except ApiException as exc:
            logger.warning("kubernetes_failed_to_collect_events: %s", exc.reason)
            return []
        except Exception as exc:  # noqa: BLE001
            logger.warning("kubernetes_failed_to_collect_events: %s", exc)
            return []

        if events is None:
            logger.warning(
                "kubernetes_no_events_collected",
                namespace=namespace,
                pod=pod,
            )
            return []

        warnings = []
        for event_item in events.items:
            if event_item.type != "Warning":
                continue

            warnings.append(
                Event(
                    type=event_item.type,
                    reason=event_item.reason,
                    message=event_item.message,
                    last_timestamp=(
                        event_item.last_timestamp.timestamp()
                        if event_item.last_timestamp
                        else None
                    ),
                )
            )

        return warnings

    def _collect_resources(self, pod_info: V1Pod) -> PodResources:
        containers = []

        for container in pod_info.spec.containers or []:
            resources = container.resources
            limits = resources.limits or {}
            req = resources.requests or {}

            containers.append(
                ContainerResources(
                    name=container.name,
                    cpu_limit=parse_cpu_quantity(limits.get("cpu")),
                    memory_limit=parse_memory_quantity(limits.get("memory")),
                    cpu_request=parse_cpu_quantity(req.get("cpu")),
                    memory_request=parse_memory_quantity(req.get("memory")),
                )
            )

        return PodResources(containers=containers)

    @staticmethod
    def _empty_snapshot(namespace: str, pod: str) -> KubernetesSnapshot:
        return KubernetesSnapshot(
            namespace=namespace,
            pod=pod,
            phase="Unknown",
            logs=LogSnapshot(
                source="kubernetes",
                lines=[],
            ),
            containers=[],
            events=[],
            resources=PodResources(containers=[]),
            metrics=None,
        )

    def get_cluster_info(self) -> ClusterInfo:
        configuration = Configuration.get_default_copy()
        version = client.VersionApi().get_code()

        return ClusterInfo(
            name=configuration.host,
            kubernetes_version=version.git_version,
            node_count=len(self.v1.list_node().items),
            namespace_count=len(self.v1.list_namespace().items),
            api_server=configuration.host,
        )

    def count_nodes(self) -> int:
        nodes = self.v1.list_node()

        return len(nodes.items)

    def count_pods(self) -> int:
        pods = self.v1.list_pod_for_all_namespaces()

        return len(pods.items)
