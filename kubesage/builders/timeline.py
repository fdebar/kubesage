from datetime import datetime

from kubesage.models.container import ContainerSnapshot
from kubesage.models.event import Event
from kubesage.models.finding import ResourceRef, Severity
from kubesage.models.incident import Incident
from kubesage.models.log import LogEntry
from kubesage.models.prometheus import MetricChange
from kubesage.models.timeline import (
    TimelineEvent,
    TimelineEventSource,
    TimelineEventType,
)


class TimelineBuilder:
    """Builds a chronological timeline from incident data."""

    def build(
        self,
        incident: Incident,
        metric_changes: list[MetricChange] | None = None,
    ) -> list[TimelineEvent]:
        events: list[TimelineEvent] = []

        for index, event in enumerate(incident.events):
            if event.last_timestamp is None:
                continue

            events.append(
                self._build_kubernetes_event(
                    incident,
                    event,
                    index,
                    event.last_timestamp,
                )
            )

        for container in incident.containers:
            events.extend(self._build_container_events(incident, container))

        for index, change in enumerate(metric_changes or []):
            events.append(self._build_metric_change_event(incident, change, index))

        events.extend(self._build_log_events(incident))

        return sorted(events, key=lambda event: event.timestamp)

    def _build_metric_change_event(
        self,
        incident: Incident,
        change: MetricChange,
        index: int,
    ) -> TimelineEvent:
        return TimelineEvent(
            id=f"metric-change-{index}",
            timestamp=change.timestamp,
            type=TimelineEventType.METRIC_CHANGE,
            source=TimelineEventSource.PROMETHEUS,
            title=self._metric_change_title(change),
            description=self._metric_change_description(change),
            severity=Severity.INFO,
            resource=self._pod_resource(incident=incident),
            metadata={
                "metric": change.metric_name,
                "previous_value": change.previous_value,
                "value": change.value,
                "labels": change.labels,
            },
        )

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

    def _build_log_events(self, incident: Incident) -> list[TimelineEvent]:
        if incident.loki_logs is None:
            return []

        events: list[TimelineEvent] = []
        for index, entry in enumerate(incident.loki_logs.entries):
            severity = self._log_severity(entry)

            if severity is None:
                continue

            events.append(
                TimelineEvent(
                    id=f"loki-log-{index}",
                    timestamp=entry.timestamp,
                    type=TimelineEventType.LOG_EVENT,
                    source=TimelineEventSource.LOKI,
                    title=self._log_title(severity),
                    description=entry.message,
                    severity=severity,
                    resource=self._pod_resource(incident),
                    metadata={
                        "labels": entry.labels,
                    },
                )
            )

        return events

    @staticmethod
    def _log_severity(entry: LogEntry) -> Severity | None:
        message = entry.message.lstrip().upper()
        if (
            message.startswith("FATAL")
            or message.startswith("CRITICAL")
            or message.startswith("ERROR")
        ):
            return Severity.ERROR

        if message.startswith("WARN") or message.startswith("WARNING"):
            return Severity.WARNING

        return None

    @staticmethod
    def _log_title(severity: Severity) -> str:
        if severity == Severity.ERROR:
            return "Application error"

        return "Application warning"

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

    @staticmethod
    def _metric_change_title(change: MetricChange) -> str:
        direction = "increased" if change.value > change.previous_value else "decreased"

        return f"{change.metric_name} {direction}"

    @staticmethod
    def _metric_change_description(change: MetricChange) -> str:
        direction = "increased" if change.value > change.previous_value else "decreased"

        return (
            f"{change.metric_name} {direction} "
            f"from {change.previous_value:g} "
            f"to {change.value:g}."
        )
