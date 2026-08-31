from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class LogSource(StrEnum):
    KUBERNETES = "kubernetes"
    LOKI = "loki"


class LogQueryType(StrEnum):
    ALL = "all"
    ERRORS = "errors"
    WARNINGS = "warnings"


@dataclass(slots=True)
class LogEntry:
    timestamp: datetime
    message: str
    labels: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class LogSnapshot:
    source: str
    entries: list[LogEntry] = field(default_factory=list)
    collected_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def line_count(self) -> int:
        return len(self.entries)

    @property
    def content(self) -> str:
        return "\n".join(entry.message for entry in self.entries)

    def tail(self, limit: int = 100) -> str:
        return "\n".join(entry.message for entry in self.entries[-limit:])
