from dataclasses import dataclass
from uuid import uuid4


@dataclass
class ExecutionContext:
    request_id: str

    @classmethod
    def create(cls) -> "ExecutionContext":
        return cls(request_id=str(uuid4())[:8])
