from abc import ABC
from abc import abstractmethod
from models.incident import Incident
from models.finding import Finding


class BaseRule(ABC):
    name = "base"
    description = ""
    enabled = True

    @abstractmethod
    def evaluate(
        self,
        incident: Incident,
    ) -> list[Finding]:
        pass
