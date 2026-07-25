from kubesage.models.finding import Finding


class SummaryBuilder:
    def build(self, findings: list[Finding]) -> str:
        if not findings:
            return "No issue detected."

        return "\n".join(f"- {finding.title}" for finding in findings)
