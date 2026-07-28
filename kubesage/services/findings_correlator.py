from kubesage.analyzers.correlation_loader import (
    discover_correlations,
)
from kubesage.models.finding import Finding


class FindingsCorrelator:
    def __init__(self) -> None:
        self.correlations = discover_correlations()

    def correlate(
        self,
        findings: list[Finding],
    ) -> list[Finding]:

        for correlation in self.correlations:
            findings = correlation.apply(findings)

        return findings
