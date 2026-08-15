import structlog
from opentelemetry import trace

from kubesage.analyzers.correlations.correlation_loader import discover_correlations
from kubesage.analyzers.rules.rule_loader import discover_rules
from kubesage.models.finding import Finding
from kubesage.models.incident import Incident
from kubesage.services.findings_correlator import FindingsCorrelator

logger = structlog.get_logger()

tracer = trace.get_tracer(__name__)


class DiagnosticEngine:
    def __init__(self, correlator: FindingsCorrelator | None = None) -> None:
        self.rules = discover_rules()
        self.correlations = discover_correlations()
        self.correlator = correlator or FindingsCorrelator()

        logger.info("rules_loaded", rules_count=len(self.rules))
        logger.info("correlations_loaded", correlations_count=len(self.correlations))

    def analyze(self, incident: Incident) -> list[Finding]:
        findings = []

        for rule in self.rules:
            with tracer.start_as_current_span(f"rules.{rule.name}") as span:
                span.set_attribute("rule.name", rule.name)
                span.set_attribute("k8s.namespace", incident.namespace)
                span.set_attribute("k8s.pod.name", incident.pod)

                rule_findings = rule.evaluate(incident)

                span.set_attribute("rule.findings.count", len(rule_findings))

                findings.extend(rule_findings)
        findings = self.correlator.correlate(findings)

        if not findings:
            logger.warning(
                "no_findings", namespace=incident.namespace, pod=incident.pod
            )

        return findings

    def list_rules(self) -> None:
        for rule in self.rules:
            print(f"- {rule.name}: {rule.description}")

    def list_correlations(self) -> None:
        for correlation in self.correlations:
            print(f"- {correlation.name}: {correlation.description}")
