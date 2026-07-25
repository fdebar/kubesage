import structlog

from kubesage.analyzers.rule_loader import discover_rules
from kubesage.models.finding import Finding
from kubesage.models.incident import Incident

logger = structlog.get_logger()


class DiagnosticEngine:
    def __init__(self) -> None:
        self.rules = discover_rules()
        logger.info("rules_loaded", rules_count=len(self.rules))

    def analyze(self, incident: Incident) -> list[Finding]:
        findings = []

        for rule in self.rules:
            findings.extend(rule.evaluate(incident))

        if not findings:
            logger.warning(
                "no_findings", namespace=incident.namespace, pod=incident.pod
            )

        return findings

    def list_rules(self) -> None:
        for rule in self.rules:
            print(f"- {rule.name}: {rule.description}")
