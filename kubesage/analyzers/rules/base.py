from abc import ABC, abstractmethod
from enum import StrEnum

from kubesage.models.finding import Finding, ResourceRef
from kubesage.models.incident import Incident


class RuleCategory(StrEnum):
    CONTAINER = "container"
    POD = "pod"
    EVENT = "event"
    METRIC = "metric"
    LOG = "log"


class BaseRule(ABC):
    """Base class for every diagnostic rule."""

    @property
    def name(self) -> str:
        return self.__class__.__name__

    description = ""
    enabled = True

    @abstractmethod
    def evaluate(
        self,
        incident: Incident,
    ) -> list[Finding]:
        pass

    def _pod_resource(self, incident: Incident) -> ResourceRef:
        return ResourceRef(
            api_version="v1",
            kind="Pod",
            namespace=incident.namespace,
            name=incident.pod,
        )
