from typing import Protocol

from kubesage.models.log import LogSnapshot


class LogProvider(Protocol):
    def collect(
        self,
        namespace: str,
        pod: str,
    ) -> LogSnapshot | None:
        """Collect logs for a pod."""
        ...
