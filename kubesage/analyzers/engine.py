from kubesage.analyzers.rule_loader import discover_rules
from kubesage.models.incident import Incident
from kubesage.models.finding import Finding
from kubesage.observability.factory import get_logger

logger = get_logger(__name__)


class DiagnosticEngine:
    def __init__(self) -> None:
        self.rules = discover_rules()
        logger.info("Loaded %d rules...", len(self.rules))

    def analyze(self, incident: Incident) -> list[Finding]:
        findings = []

        for rule in self.rules:
            findings.extend(rule.evaluate(incident))

        if not findings:
            logger.info(
                f"No findings detected for pod: {incident.pod} in namespace: {incident.namespace}"
            )

        return findings

    def list_rules(self) -> None:
        for rule in self.rules:
            print(f"- {rule.name}: {rule.description}")
