from config import logger
from analyzers.rule_loader import discover_rules
from models.incident import Incident
from models.finding import Finding


class DiagnosticEngine:
    def __init__(self) -> None:
        self.rules = discover_rules()
        logger.info("Loaded %d rules", len(self.rules))

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
