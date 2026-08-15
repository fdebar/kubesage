from opentelemetry import trace

from kubesage.analyzers.correlations.correlation_loader import (
    discover_correlations,
)
from kubesage.models.finding import Finding

tracer = trace.get_tracer(__name__)


class FindingsCorrelator:
    def __init__(self) -> None:
        self.correlations = discover_correlations()

    def correlate(self, findings: list[Finding]) -> list[Finding]:
        """
        Applies all correlations to a list of findings.
        """

        with tracer.start_as_current_span("findings.correlate") as span:
            span.set_attribute("findings.input.count", len(findings))

            for correlation in self.correlations:
                with tracer.start_as_current_span(
                    f"correlation.{correlation.name}"
                ) as sub_span:
                    sub_span.set_attribute("correlation.name", correlation.name)

                    before = len(findings)
                    findings = correlation.apply(findings)

                    sub_span.set_attribute("findings.before.count", before)
                    sub_span.set_attribute("findings.after.count", len(findings))

            findings = self._remove_duplicates(findings)

            span.set_attribute("findings.output.count", len(findings))

            return findings

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
