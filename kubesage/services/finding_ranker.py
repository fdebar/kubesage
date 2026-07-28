from kubesage.models.finding import Finding, FindingKind


class FindingRanker:
    def rank(self, findings: list[Finding]) -> list[Finding]:
        return sorted(findings, key=self._score, reverse=True)

    def _score(self, finding: Finding) -> int:
        score = finding.priority
        if finding.kind == FindingKind.DIAGNOSIS:
            score += 50

        score += finding.severity.weight * 10
        score += int(finding.confidence * 10)

        return score
