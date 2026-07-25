from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


@dataclass(slots=True)
class LogSnapshot:
    source: str
    lines: list[str] = field(default_factory=list)
    collected_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def line_count(self) -> int:
        return len(self.lines)

    @property
    def content(self) -> str:
        return "\n".join(self.lines)

    def tail(self, limit: int = 100) -> str:
        return "\n".join(self.lines[-limit:])


class LogSource(Enum):
    KUBERNETES = "kubernetes"
    LOKI = "loki"
