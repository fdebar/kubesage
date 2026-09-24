from datetime import UTC, datetime, timedelta
from threading import Lock

from kubesage.watchers.models.incident_trigger import IncidentTrigger


class IncidentDeduplicator:
    """
    Prevents the same Kubernetes watch event from being processed twice.

    The identity of an event is:
        namespace
        pod UID
        resourceVersion
        reason

    TTL is only used to limit in-memory cache retention.
    """

    def __init__(self, ttl_seconds: int = 600) -> None:
        self.ttl = timedelta(seconds=ttl_seconds)
        self._cache: dict[tuple[str, str, str, str], datetime] = {}
        self._lock = Lock()

    def should_process(self, trigger: IncidentTrigger) -> bool:
        now = datetime.now(UTC)

        with self._lock:
            self._cleanup(now)

            key = self._build_key(trigger)
            if key in self._cache:
                return False

            self._cache[key] = now
            return True

    def forget(self, trigger: IncidentTrigger) -> None:
        """
        Removes an event from the deduplication cache.

        Used when processing ultimately fails and the event may be retried
        if it is replayed by Kubernetes.
        """

        with self._lock:
            self._cache.pop(self._build_key(trigger), None)

    def _build_key(self, trigger: IncidentTrigger) -> tuple[str, str, str, str]:
        return (
            trigger.namespace,
            trigger.pod_uid,
            trigger.resource_version,
            trigger.reason,
        )

    def _cleanup(self, now: datetime) -> None:
        expired = [
            key for key, timestamp in self._cache.items() if now - timestamp > self.ttl
        ]

        for key in expired:
            del self._cache[key]
