from collections import Counter
from datetime import timedelta

from kubesage.models.finding import Finding, Severity
from kubesage.models.timeline import TimelineEvent, TimelineEventType
from kubesage.utils.config import settings


class TimelineSelector:
    def select(
        self,
        timeline: list[TimelineEvent],
        findings: list[Finding],
    ) -> list[TimelineEvent]:
        if not timeline:
            return []

        important_events = [event for event in timeline if self._is_important(event)]
        important_events.extend(self._events_related_to_findings(timeline, findings))
        important_events = list(
            {event.id: event for event in important_events}.values()
        )
        important_events = self._deduplicate_events(important_events)
        important_events = self._aggregate_error_events(important_events)

        selected = self._select_with_context(timeline, important_events)
        selected = self._deduplicate_events(selected)

        return self._limit_events(selected)

    def _is_important(self, event: TimelineEvent) -> bool:
        if event.severity in {
            Severity.CRITICAL,
            Severity.ERROR,
            Severity.WARNING,
        }:
            return True

        if event.type in {
            TimelineEventType.POD_RESTART,
            TimelineEventType.CONTAINER_TERMINATED,
            TimelineEventType.CONTAINER_STARTED,
            TimelineEventType.KUBERNETES_EVENT,
            TimelineEventType.METRIC_ANOMALY,
            TimelineEventType.METRIC_CHANGE,
            TimelineEventType.FINDING,
        }:
            return True

        return bool(event.metadata.get("error_kind")) or bool(
            event.metadata.get("error_domain")
        )

    def _events_related_to_findings(
        self,
        timeline: list[TimelineEvent],
        findings: list[Finding],
    ) -> list[TimelineEvent]:
        selected: list[TimelineEvent] = []

        if not findings:
            return []

        finding_titles = {finding.title.lower() for finding in findings}
        finding_rules = {finding.rule.lower() for finding in findings}

        for event in timeline:
            searchable = " ".join(
                value.lower()
                for value in (
                    event.title,
                    event.description or "",
                    str(event.metadata),
                )
            )

            if any(value in searchable for value in finding_titles | finding_rules):
                selected.append(event)

        return selected

    def _aggregate_error_events(
        self,
        events: list[TimelineEvent],
    ) -> list[TimelineEvent]:
        """
        Collapse repetitive application error logs into representative
        events for the AI-facing timeline.

        Raw timeline events are never modified.

        Events are grouped by:
        - event type
        - source
        - resource

        Different containers, error kinds and messages can therefore belong
        to the same error episode when they occur close enough in time.
        """

        error_events = [
            event for event in events if self._is_aggregatable_error_event(event)
        ]

        if not error_events:
            return events

        clusters: list[list[TimelineEvent]] = []
        current_cluster: list[TimelineEvent] = []
        aggregated: list[TimelineEvent] = []

        error_events = sorted(error_events, key=lambda event: event.timestamp)
        for event in error_events:
            if not current_cluster:
                current_cluster = [event]
                continue

            previous = current_cluster[-1]
            if self._can_join_error_cluster(previous, event):
                current_cluster.append(event)
            else:
                clusters.append(current_cluster)
                current_cluster = [event]

        if current_cluster:
            clusters.append(current_cluster)

        for cluster in clusters:
            if len(cluster) == 1:
                aggregated.append(cluster[0])
            else:
                aggregated.append(self._build_aggregated_error_event(cluster))

        return aggregated

    def _is_aggregatable_error_event(self, event: TimelineEvent) -> bool:
        if event.type != TimelineEventType.LOG_EVENT:
            return False

        return bool(
            event.metadata.get("error_kind") or event.metadata.get("error_domain")
        )

    def _can_join_error_cluster(
        self,
        previous: TimelineEvent,
        current: TimelineEvent,
    ) -> bool:
        cluster_window = timedelta(
            seconds=settings.ai_timeline_error_cluster_window_seconds
        )

        if current.timestamp - previous.timestamp > cluster_window:
            return False

        return self._error_cluster_key(previous) == self._error_cluster_key(current)

    def _error_cluster_key(self, event: TimelineEvent) -> tuple[str, str, str]:
        resource = ""

        if event.resource:
            resource = ":".join(
                value
                for value in (
                    getattr(event.resource, "namespace", None),
                    getattr(event.resource, "kind", None),
                    getattr(event.resource, "name", None),
                )
                if value
            )

        return (event.type.value, event.source.value, resource)

    def _build_aggregated_error_event(
        self,
        events: list[TimelineEvent],
    ) -> TimelineEvent:
        representative = events[0]

        first_seen = events[0].timestamp
        last_seen = events[-1].timestamp

        error_kinds = Counter(
            str(event.metadata.get("error_kind", "unknown")) for event in events
        )

        messages = [event.description for event in events if event.description]

        metadata = dict(representative.metadata)
        metadata["aggregated"] = True
        metadata["occurrences"] = len(events)
        metadata["first_seen"] = first_seen.isoformat()
        metadata["last_seen"] = last_seen.isoformat()
        metadata["error_kinds"] = dict(error_kinds)
        metadata["aggregated_event_ids"] = [event.id for event in events]
        metadata.pop("error_kind", None)

        return TimelineEvent(
            id=f"aggregated-error-{representative.id}",
            timestamp=first_seen,
            type=representative.type,
            source=representative.source,
            title="Repeated application errors",
            description=self._build_aggregated_error_description(
                events=events,
                error_kinds=error_kinds,
                messages=messages,
            ),
            severity=max(
                (event.severity for event in events),
                key=self._severity_rank,
            ),
            resource=representative.resource,
            metadata=metadata,
        )

    def _build_aggregated_error_description(
        self,
        events: list[TimelineEvent],
        error_kinds: Counter[str],
        messages: list[str],
    ) -> str:
        first_seen = events[0].timestamp
        last_seen = events[-1].timestamp

        kinds = ", ".join(
            f"{kind}: {count}" for kind, count in error_kinds.most_common()
        )

        lines = [
            f"{len(events)} application error occurrences.",
            f"Error kinds: {kinds}.",
            f"First seen: {first_seen.isoformat()}",
            f"Last seen: {last_seen.isoformat()}",
        ]

        if messages:
            lines.append(f"Example: {messages[0]}")

        return " ".join(lines)

    def _severity_rank(
        self,
        severity: Severity,
    ) -> int:
        return {
            Severity.CRITICAL: 4,
            Severity.ERROR: 3,
            Severity.WARNING: 2,
            Severity.INFO: 1,
        }.get(severity, 0)

    def _select_with_context(
        self,
        timeline: list[TimelineEvent],
        important_events: list[TimelineEvent],
    ) -> list[TimelineEvent]:
        if not important_events:
            return []

        before = timedelta(
            seconds=settings.ai_timeline_window_before_seconds,
        )
        after = timedelta(
            seconds=settings.ai_timeline_window_after_seconds,
        )

        aggregated_raw_ids: set[str] = set()

        for important in important_events:
            raw_ids = important.metadata.get("aggregated_event_ids")

            if isinstance(raw_ids, list):
                aggregated_raw_ids.update(str(event_id) for event_id in raw_ids)

        selected_ids: set[str] = set()

        for event in important_events:
            if event.metadata.get("aggregated") is True:
                continue

            if event.id not in aggregated_raw_ids:
                selected_ids.add(event.id)

        for event in timeline:
            if event.id in aggregated_raw_ids:
                continue

            if event.type == TimelineEventType.LOG_EVENT and not self._is_important(
                event
            ):
                continue

            for important in important_events:
                if (
                    important.timestamp - before
                    <= event.timestamp
                    <= important.timestamp + after
                ):
                    selected_ids.add(event.id)
                    break

        selected = [
            event
            for event in timeline
            if event.id in selected_ids and event.id not in aggregated_raw_ids
        ]

        synthetic_events = [
            event
            for event in important_events
            if event.metadata.get("aggregated") is True
        ]

        selected.extend(synthetic_events)

        return sorted(selected, key=lambda event: event.timestamp)

    def _deduplicate_events(self, events: list[TimelineEvent]) -> list[TimelineEvent]:
        seen: set[tuple[str, str, str]] = set()
        result: list[TimelineEvent] = []

        for event in events:
            if event.type == TimelineEventType.LOG_EVENT:
                result.append(event)
                continue

            key = (
                event.type.value,
                event.source.value,
                event.title,
            )

            if event.severity == Severity.INFO and key in seen:
                continue

            seen.add(key)
            result.append(event)

        return result

    def _limit_events(self, events: list[TimelineEvent]) -> list[TimelineEvent]:
        ranked = sorted(events, key=self._score, reverse=True)
        selected = ranked[: settings.ai_timeline_max_events]

        return sorted(selected, key=lambda event: event.timestamp)

    def _score(self, event: TimelineEvent) -> int:
        score = 0

        if event.severity == Severity.CRITICAL:
            score += 100
        elif event.severity == Severity.ERROR:
            score += 80
        elif event.severity == Severity.WARNING:
            score += 50
        else:
            score += 5

        score += {
            TimelineEventType.POD_RESTART: 80,
            TimelineEventType.CONTAINER_TERMINATED: 70,
            TimelineEventType.CONTAINER_STARTED: 40,
            TimelineEventType.KUBERNETES_EVENT: 60,
            TimelineEventType.METRIC_ANOMALY: 60,
            TimelineEventType.METRIC_CHANGE: 40,
            TimelineEventType.FINDING: 70,
        }.get(event.type, 0)

        if event.metadata.get("error_kind"):
            score += 60

        if event.metadata.get("error_domain"):
            score += 30

        if event.metadata.get("aggregated"):
            score += 60

        occurrences = event.metadata.get("occurrences")
        if isinstance(occurrences, int) and occurrences > 1:
            score += min(occurrences * 5, 50)

        return score
