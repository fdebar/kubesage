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
        important_events = self._deduplicate_events(important_events)

        selected = self._select_with_context(
            timeline=timeline,
            important_events=important_events,
        )
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

    def _select_with_context(
        self,
        timeline: list[TimelineEvent],
        important_events: list[TimelineEvent],
    ) -> list[TimelineEvent]:
        if not important_events:
            return []

        before = timedelta(seconds=settings.ai_timeline_window_before_seconds)
        after = timedelta(seconds=settings.ai_timeline_window_after_seconds)
        selected_ids = {event.id for event in important_events}

        for event in timeline:
            for important in important_events:
                if (
                    important.timestamp - before
                    <= event.timestamp
                    <= important.timestamp + after
                ):
                    selected_ids.add(event.id)
                    break

        return [event for event in timeline if event.id in selected_ids]

    def _deduplicate_events(self, events: list[TimelineEvent]) -> list[TimelineEvent]:
        seen: set[tuple[str, str, str]] = set()
        result: list[TimelineEvent] = []

        for event in events:
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
        if len(events) <= settings.ai_timeline_max_events:
            return events

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

        return score
