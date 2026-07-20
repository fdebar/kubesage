from analyzers.rules.crashloop import CrashLoopRule
from analyzers.rules.oom import OOMRule
from analyzers.rules.connectivity import ConnectivityRule


class DiagnosticEngine:

    def __init__(self):

        self.rules = [
            CrashLoopRule(),
            OOMRule(),
            ConnectivityRule(),
        ]

    def analyze(self, incident):

        findings = []

        for rule in self.rules:

            findings.extend(rule.evaluate(incident))

        return findings
