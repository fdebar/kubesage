from datetime import UTC, datetime, timedelta
from threading import Lock

from kubesage.watchers.models.incident_trigger import IncidentTrigger


class IncidentDeduplicator:
    """
    Suppresses repeated analyses for the same Pod and incident reason during
    a cooldown window.

    The deduplication identity is:
        namespace
        pod UID
        reason

    The resourceVersion identifies a watch event, but a CrashLoopBackOff
    produces a new resourceVersion on each restart. It is therefore not part
    of the cooldown key.
    """

    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl = timedelta(seconds=ttl_seconds)
        self._cache: dict[tuple[str, str, str], datetime] = {}
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

    def _build_key(self, trigger: IncidentTrigger) -> tuple[str, str, str]:
        return (
            trigger.namespace,
            trigger.pod_uid,
            trigger.reason,
        )

    def _cleanup(self, now: datetime) -> None:
        expired = [
            key for key, timestamp in self._cache.items() if now - timestamp > self.ttl
        ]

        for key in expired:
            del self._cache[key]
