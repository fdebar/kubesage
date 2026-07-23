from typing import Any

import structlog
from kubernetes.client.exceptions import ApiException

from kubesage.models.container import ContainerInfo
from kubesage.models.events import Event
from kubesage.models.incident import Incident
from kubesage.utils.config import settings
from kubesage.utils.exceptions import PodNotFoundError
from kubesage.utils.kube_client import create_core_v1_api

logger = structlog.get_logger()


class KubernetesService:
    def __init__(self) -> None:
        self.v1 = create_core_v1_api()

    def collect(self, namespace: str, pod: str) -> Incident:
        logger.info("kubernetes_collecting_data_for_pod", namespace=namespace, pod=pod)

        if self.v1 is None:
            logger.error("kubernetes_unavailable")
            return self._empty_incident(namespace, pod)

        try:
            pod_info = self.v1.read_namespaced_pod(name=pod, namespace=namespace)
        except ApiException as exc:
            if exc.status == 404:
                raise PodNotFoundError(
                    f"Pod '{pod}' not found in namespace '{namespace}'."
                ) from None
            else:
                logger.error(
                    "kubernetes_api_error", status=exc.status, reason=exc.reason
                )
            return self._empty_incident(namespace, pod)
        except Exception as exc:  # noqa: BLE001
            logger.error("kubernetes_failed_to_collect_data: %s", exc)
            return self._empty_incident(namespace, pod)

        logs = self._collect_logs(namespace, pod)
        containers = self._collect_containers(pod_info)
        events = self._collect_events(namespace, pod)

        return Incident(
            namespace=namespace,
            pod=pod,
            phase=pod_info.status.phase or "Unknown",
            logs=logs,
            containers=containers,
            events=events,
        )

    def _collect_logs(self, namespace: str, pod: str) -> str:
        if self.v1 is None:
            return ""
        try:
            logs = self.v1.read_namespaced_pod_log(
                name=pod,
                namespace=namespace,
                tail_lines=settings.log_tail_lines,
            )
        except ApiException as exc:
            logger.warning("kubernetes_failed_to_collect_logs: %s", exc.reason)
            return ""
        except Exception as exc:  # noqa: BLE001
            logger.warning("kubernetes_failed_to_collect_logs: %s", exc)
            return ""

        if isinstance(logs, bytes):
            return logs.decode("utf-8")

        return logs or ""

    def _collect_containers(self, pod_info: Any) -> list[ContainerInfo]:
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
                ContainerInfo(
                    name=container.name,
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

    @staticmethod
    def _empty_incident(namespace: str, pod: str) -> Incident:
        return Incident(
            namespace=namespace,
            pod=pod,
            phase="Unknown",
            logs="",
            containers=[],
            events=[],
        )
