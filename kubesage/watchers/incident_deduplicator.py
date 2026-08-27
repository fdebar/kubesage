from datetime import UTC, datetime, timedelta

from kubesage.watchers.models.incident_trigger import IncidentTrigger


class IncidentDeduplicator:
    """
    Prevents duplicate incident analyses during a cooldown window.
    """

    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl = timedelta(seconds=ttl_seconds)
        self._cache: dict[str, datetime] = {}

    def should_process(self, trigger: IncidentTrigger) -> bool:
        now = datetime.now(UTC)
        self._cleanup(now)
        key = self._build_key(trigger)
        last_seen = self._cache.get(key)
        if last_seen is not None:
            return False
        self._cache[key] = now
        return True

    def _build_key(self, trigger: IncidentTrigger) -> str:
        return f"{trigger.namespace}:{trigger.pod_uid}:{trigger.reason}"

    def _cleanup(self, now: datetime) -> None:
        expired = [
            key for key, timestamp in self._cache.items() if now - timestamp > self.ttl
        ]

        for key in expired:
            del self._cache[key]
