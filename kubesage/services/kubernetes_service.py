from typing import Any

import structlog
from kubernetes.client.exceptions import ApiException

from kubesage.models.container import (
    ContainerResources,
    ContainerStatus,
    PodResources,
)
from kubesage.models.events import Event
from kubesage.models.kubernetes_snapshot import KubernetesSnapshot
from kubesage.models.log import LogSnapshot
from kubesage.providers.kubernetes_provider import KubernetesProvider
from kubesage.utils.config import settings
from kubesage.utils.exceptions import PodNotFoundError
from kubesage.utils.kube_client import create_core_v1_api

logger = structlog.get_logger()


class KubernetesService(KubernetesProvider):
    def __init__(self) -> None:
        self.v1 = create_core_v1_api()

    def collect(self, namespace: str, pod: str) -> KubernetesSnapshot:
        logger.info("kubernetes_collecting_data_for_pod", namespace=namespace, pod=pod)

        if self.v1 is None:
            logger.warning("kubernetes_metrics_unavailable")
            return self._empty_snapshot(namespace, pod)

        try:
            pod_info = self.v1.read_namespaced_pod(name=pod, namespace=namespace)
        except ApiException as exc:
            if exc.status == 404:
                logger.warning(
                    "kubernetes_pod_not_found",
                    namespace=namespace,
                    pod=pod,
                )
                raise PodNotFoundError(
                    f"Pod '{pod}' not found in namespace '{namespace}'."
                ) from None
            return self._empty_snapshot(namespace, pod)
        except Exception as exc:  # noqa: BLE001
            logger.error("kubernetes_failed_to_collect_data: %s", exc)
            return self._empty_snapshot(namespace, pod)

        logs = self._collect_logs(namespace, pod)
        containers = self._collect_containers(pod_info)
        events = self._collect_events(namespace, pod)
        resources = self._collect_resources(pod_info)

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
        if self.v1 is None:
            return LogSnapshot(source="kubernetes")

        try:
            logs = self.v1.read_namespaced_pod_log(
                name=pod,
                namespace=namespace,
                tail_lines=settings.log_tail_lines,
            )
        except ApiException as exc:
            logger.warning("kubernetes_failed_to_collect_logs: %s", exc.reason)
            raise PodNotFoundError(
                f"Pod '{pod}' not found in namespace '{namespace}'."
            ) from None
        except Exception as exc:  # noqa: BLE001
            logger.warning("kubernetes_failed_to_collect_logs: %s", exc)

        if isinstance(logs, bytes):
            logs = logs.decode("utf-8")

        return LogSnapshot(
            source="kubernetes",
            lines=logs.split("\n") if logs else [],
        )

    def _collect_containers(self, pod_info: Any) -> list[ContainerStatus]:
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
        if self.v1 is None:
            return []
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
                        str(event_item.last_timestamp)
                        if event_item.last_timestamp
                        else ""
                    ),
                )
            )

        return warnings

    def _collect_resources(
        self,
        pod_info: Any,
    ) -> PodResources:
        containers = []

        for container in pod_info.spec.containers or []:
            resources = container.resources
            limits = resources.limits or {}
            req = resources.requests or {}

            containers.append(
                ContainerResources(
                    name=container.name,
                    cpu_limit=self._parse_cpu(limits.get("cpu")),
                    memory_limit=self._parse_memory(limits.get("memory")),
                    cpu_request=self._parse_cpu(req.get("cpu")),
                    memory_request=self._parse_memory(req.get("memory")),
                )
            )
        logger.debug("kubernetes_collecting_resources_result", containers=containers)

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

    @staticmethod
    def _parse_cpu(
        value: str | None,
    ) -> float | None:
        if value is None:
            return None

        if value.endswith("m"):
            return float(value[:-1]) / 1000

        return float(value)

    @staticmethod
    def _parse_memory(
        value: str | None,
    ) -> int | None:
        if value is None:
            return None

        multipliers = {
            "Ki": 1024,
            "Mi": 1024**2,
            "Gi": 1024**3,
            "Ti": 1024**4,
        }

        for suffix, multiplier in multipliers.items():
            if value.endswith(suffix):
                return int(float(value[: -len(suffix)]) * multiplier)

        return int(value)
