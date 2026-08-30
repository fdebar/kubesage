from datetime import datetime

from kubesage.models.container import ContainerSnapshot
from kubesage.models.event import Event
from kubesage.models.finding import ResourceRef, Severity
from kubesage.models.incident import Incident
from kubesage.models.timeline import (
    TimelineEvent,
    TimelineEventSource,
    TimelineEventType,
)


class TimelineBuilder:
    """Builds a chronological timeline from incident data."""

    def build(self, incident: Incident) -> list[TimelineEvent]:
        events: list[TimelineEvent] = []

        for index, event in enumerate(incident.events):
            if event.last_timestamp is None:
                continue

            events.append(
                self._build_kubernetes_event(
                    incident=incident,
                    event=event,
                    index=index,
                    timestamp=event.last_timestamp,
                )
            )

        for container in incident.containers:
            events.extend(
                self._build_container_events(
                    incident=incident,
                    container=container,
                )
            )

        return sorted(events, key=lambda event: event.timestamp)

    def _build_kubernetes_event(
        self,
        incident: Incident,
        event: Event,
        index: int,
        timestamp: datetime,
    ) -> TimelineEvent:
        return TimelineEvent(
            id=f"kubernetes-event-{index}",
            timestamp=timestamp,
            type=TimelineEventType.KUBERNETES_EVENT,
            source=TimelineEventSource.KUBERNETES,
            title=event.reason,
            description=event.message,
            severity=self._severity_from_event(event),
            resource=ResourceRef(
                api_version="v1",
                kind="Pod",
                namespace=incident.namespace,
                name=incident.pod,
            ),
            metadata={
                "event_type": event.type,
                "reason": event.reason,
            },
        )

    def _build_container_events(
        self,
        incident: Incident,
        container: ContainerSnapshot,
    ) -> list[TimelineEvent]:
        events: list[TimelineEvent] = []

        if container.started_at is not None:
            events.append(
                self._build_container_started_event(
                    incident=incident,
                    container=container,
                    timestamp=container.started_at,
                )
            )

        if container.finished_at is not None:
            events.append(
                self._build_container_terminated_event(
                    incident=incident,
                    container=container,
                    timestamp=container.finished_at,
                )
            )

        return events

    def _build_container_started_event(
        self,
        incident: Incident,
        container: ContainerSnapshot,
        timestamp: datetime,
    ) -> TimelineEvent:
        return TimelineEvent(
            id=f"container-started-{container.name}",
            timestamp=timestamp,
            type=TimelineEventType.CONTAINER_STARTED,
            source=TimelineEventSource.KUBERNETES,
            title="Container started",
            description=f"Container '{container.name}' started.",
            severity=Severity.INFO,
            resource=self._pod_resource(incident),
            metadata={"container": container.name},
        )

    def _build_container_terminated_event(
        self,
        incident: Incident,
        container: ContainerSnapshot,
        timestamp: datetime,
    ) -> TimelineEvent:
        return TimelineEvent(
            id=f"container-terminated-{container.name}",
            timestamp=timestamp,
            type=TimelineEventType.CONTAINER_TERMINATED,
            source=TimelineEventSource.KUBERNETES,
            title="Container terminated",
            description=self._termination_description(container),
            severity=self._termination_severity(container),
            resource=self._pod_resource(incident),
            metadata={
                "container": container.name,
                "exit_code": container.last_exit_code,
                "reason": container.last_exit_reason,
            },
        )

    @staticmethod
    def _pod_resource(incident: Incident) -> ResourceRef:
        return ResourceRef(
            api_version="v1",
            kind="Pod",
            namespace=incident.namespace,
            name=incident.pod,
        )

    @staticmethod
    def _severity_from_event(event: Event) -> Severity:
        if event.type.lower() == "warning":
            return Severity.WARNING

        return Severity.INFO

    @staticmethod
    def _termination_description(container: ContainerSnapshot) -> str:
        if container.last_exit_reason:
            return (
                f"Container '{container.name}' terminated: "
                f"{container.last_exit_reason}."
            )

        return f"Container '{container.name}' terminated."

    @staticmethod
    def _termination_severity(container: ContainerSnapshot) -> Severity:
        reason = (container.last_exit_reason or "").lower()

        if reason == "oomkilled":
            return Severity.CRITICAL

        if reason in {"error", "failed"}:
            return Severity.ERROR

        if reason in {"crashloopbackoff", "backoff"}:
            return Severity.WARNING

        return Severity.INFO
