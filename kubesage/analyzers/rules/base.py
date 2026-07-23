from abc import ABC, abstractmethod

from kubesage.models.finding import Finding
from kubesage.models.incident import Incident


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
