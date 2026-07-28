import structlog

from kubesage.analyzers.rule_loader import discover_rules
from kubesage.models.finding import Finding
from kubesage.models.incident import Incident
from kubesage.services.findings_correlator import FindingsCorrelator

logger = structlog.get_logger()


class DiagnosticEngine:
    def __init__(
        self,
        correlator: FindingsCorrelator | None = None,
    ) -> None:
        self.rules = discover_rules()
        self.correlator = correlator or FindingsCorrelator()
        logger.info("rules_loaded", rules_count=len(self.rules))

    def analyze(self, incident: Incident) -> list[Finding]:
        findings = []

        logger.debug(
            "incident_dump",
            namespace=incident.namespace,
            pod=incident.pod,
            incident_json=incident.model_dump_json(indent=2),
        )

        for rule in self.rules:
            findings.extend(rule.evaluate(incident))
        findings = self.correlator.correlate(findings)

        if not findings:
            logger.warning(
                "no_findings", namespace=incident.namespace, pod=incident.pod
            )

        return findings

    def list_rules(self) -> None:
        for rule in self.rules:
            print(f"- {rule.name}: {rule.description}")
