import time
from datetime import UTC, datetime

import structlog
from kubernetes import client
from kubernetes.client import Configuration, V1Pod
from kubernetes.client.exceptions import ApiException
from opentelemetry.trace import Status, StatusCode, get_tracer

from kubesage.models.cluster_info import ClusterInfo
from kubesage.models.container import (
    ContainerResources,
    ContainerStatus,
    PodResources,
)
from kubesage.models.event import Event
from kubesage.models.kubernetes_snapshot import KubernetesSnapshot
from kubesage.models.log import LogEntry, LogSnapshot, LogSource
from kubesage.observability.metrics import KUBERNETES_DURATION, KUBERNETES_ERRORS
from kubesage.providers.kubernetes_provider import KubernetesProvider
from kubesage.utils.config import settings
from kubesage.utils.exceptions import PodNotFoundError
from kubesage.utils.kube_client import create_core_v1_api
from kubesage.utils.resource_quantity import parse_cpu_quantity, parse_memory_quantity

logger = structlog.get_logger()
tracer = get_tracer(__name__)


class KubernetesService(KubernetesProvider):
    """Service for collecting data from Kubernetes."""

    def __init__(self) -> None:
        self.v1 = create_core_v1_api()

    def collect(self, namespace: str, pod: str) -> KubernetesSnapshot:
        start = time.perf_counter()
        logger.info("kubernetes_starting_collecting_data", namespace=namespace, pod=pod)

        with tracer.start_as_current_span("kubernetes.collect") as span:
            span.set_attribute("k8s.namespace", namespace)
            span.set_attribute("k8s.pod.name", pod)

            with tracer.start_as_current_span("kubernetes.get_pod") as span:
                span.set_attribute("k8s.namespace", namespace)
                span.set_attribute("k8s.pod.name", pod)

                try:
                    pod_info = self.v1.read_namespaced_pod(pod, namespace)
                except ApiException as exc:
                    span.record_exception(exc)
                    span.set_status(
                        Status(
                            StatusCode.ERROR,
                            f"Kubernetes API error: {exc.status}",
                        )
                    )

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

                except Exception as exc:
                    span.record_exception(exc)
                    span.set_status(Status(StatusCode.ERROR, str(exc)))

                    KUBERNETES_ERRORS.labels(reason="Unexpected Error").inc()
                    logger.warning(
                        "kubernetes_failed_to_collect_data",
                        namespace=namespace,
                        pod=pod,
                        error_type=type(exc).__name__,
                        error=str(exc),
                    )
                    return self._empty_snapshot(namespace, pod)

            containers = self._collect_containers(pod_info)
            logs = self._collect_logs(namespace, pod, containers)
            events = self._collect_events(namespace, pod)
            resources = self._collect_resources(pod_info)
            pod_uid = pod_info.metadata.uid

            if pod_uid is None:
                raise PodNotFoundError(
                    f"Pod '{pod}' has no UID in namespace '{namespace}'."
                )

            KUBERNETES_DURATION.observe(time.perf_counter() - start)

            return KubernetesSnapshot(
                namespace=namespace,
                pod=pod,
                pod_uid=pod_uid,
                phase=pod_info.status.phase,
                logs=logs,
                containers=containers,
                events=events,
                resources=resources,
            )

    def _collect_logs(
        self,
        namespace: str,
        pod: str,
        containers: list[ContainerStatus],
    ) -> LogSnapshot:
        with tracer.start_as_current_span("kubernetes.get_logs") as span:
            span.set_attribute("k8s.namespace", namespace)
            span.set_attribute("k8s.pod.name", pod)

            collected_at = datetime.now(UTC)
            entries: list[LogEntry] = []

            for container in containers:
                try:
                    logs = self.v1.read_namespaced_pod_log(
                        name=pod,
                        namespace=namespace,
                        container=container.name,
                        tail_lines=settings.log_tail_lines,
                    )

                    if isinstance(logs, bytes):
                        logs = logs.decode("utf-8")

                    if logs:
                        entries.extend(
                            LogEntry(
                                timestamp=collected_at,
                                message=line,
                                labels={"container": container.name},
                            )
                            for line in logs.splitlines()
                        )

                except ApiException as exc:
                    span.record_exception(exc)
                    span.set_status(
                        Status(
                            StatusCode.ERROR,
                            f"Kubernetes log API error: {exc.status}",
                        )
                    )

                    logger.warning(
                        "kubernetes_failed_to_collect_logs",
                        namespace=namespace,
                        pod=pod,
                        status=exc.status,
                        reason=exc.reason,
                    )

                    if exc.status == 404:
                        raise PodNotFoundError(
                            f"Pod '{pod}' not found in namespace '{namespace}'."
                        ) from None
                except Exception as exc:
                    span.record_exception(exc)
                    span.set_status(Status(StatusCode.ERROR, str(exc)))

                    logger.warning(
                        "kubernetes_failed_to_collect_logs",
                        namespace=namespace,
                        pod=pod,
                        container=container.name,
                        error_type=type(exc).__name__,
                        error=str(exc),
                    )

            return LogSnapshot(
                source=LogSource.KUBERNETES,
                entries=entries,
                collected_at=collected_at,
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
            finished_at = None

            if container.last_state and container.last_state.terminated:
                last_exit_code = container.last_state.terminated.exit_code
                last_exit_reason = container.last_state.terminated.reason
                finished_at = container.last_state.terminated.finished_at

            started_at = None
            if container.state and container.state.running:
                started_at = container.state.running.started_at

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
                    finished_at=finished_at,
                    started_at=started_at,
                )
            )

        return containers

    def _collect_events(self, namespace: str, pod: str) -> list[Event]:
        with tracer.start_as_current_span("kubernetes.get_events") as span:
            span.set_attribute("k8s.namespace", namespace)
            span.set_attribute("k8s.pod.name", pod)

            try:
                events = self.v1.list_namespaced_event(
                    namespace=namespace,
                    field_selector=f"involvedObject.name={pod}",
                )
            except ApiException as exc:
                span.record_exception(exc)
                span.set_status(
                    Status(
                        StatusCode.ERROR,
                        f"Kubernetes events API error: {exc.status}",
                    )
                )
                logger.warning(
                    "kubernetes_failed_to_collect_events",
                    reason=exc.reason,
                    status=exc.status,
                )

                return []
            except Exception as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))

                logger.warning(
                    "kubernetes_failed_to_collect_events",
                    namespace=namespace,
                    pod=pod,
                    error_type=type(exc).__name__,
                    error=str(exc),
                )

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
                        last_timestamp=event_item.last_timestamp,
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
            pod_uid="",
            phase="Unknown",
            logs=LogSnapshot(source="kubernetes"),
            resources=PodResources(containers=[]),
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
