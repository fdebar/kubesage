from abc import ABC, abstractmethod

from models.incident import Incident
from models.finding import Finding


class BaseRule(ABC):

    @abstractmethod
    def evaluate(self, incident: Incident) -> list[Finding]:

        pass
