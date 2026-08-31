from typing import Protocol

from kubesage.models.log import LogQueryType, LogSnapshot


class LogProvider(Protocol):
    def collect(
        self,
        namespace: str,
        pod: str,
        query_type: LogQueryType,
    ) -> LogSnapshot | None:
        """Collect logs for a pod."""
        ...
