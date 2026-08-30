from datetime import datetime

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
        events = []

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

    @staticmethod
    def _severity_from_event(event: Event) -> Severity:
        if event.type.lower() == "warning":
            return Severity.WARNING

        return Severity.INFO
