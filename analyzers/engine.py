from analyzers.rules.connectivity import ConnectivityRule
from analyzers.rules.crashloop import CrashLoopRule
from analyzers.rules.high_memory import HighMemoryRule
from analyzers.rules.oom import OOMRule


class DiagnosticEngine:

    def __init__(self):

        self.rules = [
            CrashLoopRule(),
            OOMRule(),
            ConnectivityRule(),
            HighMemoryRule(),
        ]

    def analyze(self, incident):
        findings = []

        for rule in self.rules:
            findings.extend(rule.evaluate(incident))

        return findings
