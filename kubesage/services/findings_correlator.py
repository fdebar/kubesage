from kubesage.analyzers.correlations.correlation_loader import (
    discover_correlations,
)
from kubesage.models.finding import Finding


class FindingsCorrelator:
    def __init__(self) -> None:
        self.correlations = discover_correlations()

    def correlate(self, findings: list[Finding]) -> list[Finding]:
        """
        Applies all correlations to a list of findings.
        """

        for correlation in self.correlations:
            findings = correlation.apply(findings)

        return self._remove_duplicates(findings)

    def _remove_duplicates(self, findings: list[Finding]) -> list[Finding]:
        """
        Removes duplicate findings from a list of findings in case
        multiple correlations produce the same finding.
        """

        seen: set[str] = set()
        result: list[Finding] = []

        for finding in findings:
            key = finding.rule
            if key in seen:
                continue

            seen.add(key)
            result.append(finding)

        return result
