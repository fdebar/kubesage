from abc import ABC, abstractmethod

from kubesage.models.finding import Finding


class BaseCorrelation(ABC):
    """Base class for finding correlations."""

    description: str
    rule_id: str | None

    @property
    def name(self) -> str:
        return self.rule_id or self.__class__.__name__

    @abstractmethod
    def apply(self, findings: list[Finding]) -> list[Finding]:
        pass

    def _find(self, findings: list[Finding], rule: str) -> Finding | None:
        return next((finding for finding in findings if finding.rule == rule), None)

    def _has(self, findings: list[Finding], rule: str) -> bool:
        return self._find(findings, rule) is not None
