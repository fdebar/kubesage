from collections.abc import Callable, Iterable
from typing import Any

from kubernetes.client import (
    V1ContainerState,
    V1ContainerStateTerminated,
    V1ContainerStateWaiting,
    V1ContainerStatus,
    V1ObjectMeta,
    V1Pod,
    V1PodStatus,
)
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from kubesage.database.models.watcher_pod_state import WatcherPodStateModel

SessionFactory = Callable[[], Session]


class WatcherPodStateRepository:
    """Persists the subset of Pod state used by watcher change detection."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self.session_factory = session_factory

    def list_all(self) -> list[V1Pod]:
        with self.session_factory() as session:
            rows = session.execute(select(WatcherPodStateModel)).scalars().all()
            return [self._to_pod(row.namespace, row.pod_uid, row.state) for row in rows]

    def save(self, pod: V1Pod) -> None:
        metadata = pod.metadata
        if metadata is None or metadata.namespace is None or metadata.uid is None:
            return

        with self.session_factory() as session:
            row = session.get(WatcherPodStateModel, (metadata.namespace, metadata.uid))
            state = self._to_state(pod)
            if row is None:
                row = WatcherPodStateModel(
                    namespace=metadata.namespace,
                    pod_uid=metadata.uid,
                    state=state,
                )
                session.add(row)
            else:
                row.state = state
            session.commit()

    def remove(self, namespace: str, pod_uid: str) -> None:
        with self.session_factory() as session:
            session.execute(
                delete(WatcherPodStateModel).where(
                    WatcherPodStateModel.namespace == namespace,
                    WatcherPodStateModel.pod_uid == pod_uid,
                )
            )
            session.commit()

    def replace_all(self, pods: Iterable[V1Pod]) -> None:
        states: dict[tuple[str, str], dict[str, Any]] = {}
        for pod in pods:
            metadata = pod.metadata
            if metadata is None or metadata.namespace is None or metadata.uid is None:
                continue
            states[(metadata.namespace, metadata.uid)] = self._to_state(pod)

        with self.session_factory() as session:
            session.execute(delete(WatcherPodStateModel))
            session.add_all(
                WatcherPodStateModel(namespace=namespace, pod_uid=uid, state=state)
                for (namespace, uid), state in states.items()
            )
            session.commit()

    @staticmethod
    def _to_state(pod: V1Pod) -> dict[str, Any]:
        status = pod.status
        containers: list[dict[str, Any]] = []
        if status is not None and status.container_statuses:
            for container in status.container_statuses:
                waiting = container.state.waiting if container.state else None
                terminated = (
                    container.last_state.terminated if container.last_state else None
                )
                containers.append(
                    {
                        "name": container.name,
                        "image": container.image,
                        "image_id": container.image_id,
                        "ready": container.ready,
                        "restart_count": container.restart_count,
                        "waiting_reason": waiting.reason if waiting else None,
                        "last_terminated_reason": (
                            terminated.reason if terminated else None
                        ),
                    }
                )
        return {
            "name": pod.metadata.name if pod.metadata else None,
            "resource_version": (
                pod.metadata.resource_version if pod.metadata else None
            ),
            "phase": status.phase if status else None,
            "container_statuses": containers,
        }

    @staticmethod
    def _to_pod(namespace: str, pod_uid: str, state: dict[str, Any]) -> V1Pod:
        statuses = []
        for item in state.get("container_statuses", []):
            waiting_reason = item.get("waiting_reason")
            terminated_reason = item.get("last_terminated_reason")
            statuses.append(
                V1ContainerStatus(
                    name=item.get("name"),
                    image=item.get("image"),
                    image_id=item.get("image_id"),
                    ready=item.get("ready", False),
                    restart_count=item.get("restart_count", 0),
                    state=(
                        V1ContainerState(
                            waiting=V1ContainerStateWaiting(reason=waiting_reason)
                        )
                        if waiting_reason
                        else None
                    ),
                    last_state=(
                        V1ContainerState(
                            terminated=V1ContainerStateTerminated(
                                reason=terminated_reason
                            )
                        )
                        if terminated_reason
                        else None
                    ),
                )
            )

        return V1Pod(
            metadata=V1ObjectMeta(
                namespace=namespace,
                name=state.get("name"),
                uid=pod_uid,
                resource_version=state.get("resource_version"),
            ),
            status=V1PodStatus(
                phase=state.get("phase"),
                container_statuses=statuses,
            ),
        )
