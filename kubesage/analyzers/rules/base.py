from abc import ABC
from abc import abstractmethod
from kubesage.models.incident import Incident
from kubesage.models.finding import Finding


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
