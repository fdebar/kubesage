from kubesage.models.finding import Finding, FindingKind, ResourceRef, Severity
from kubesage.services.finding_ranker import FindingRanker


def test_diagnosis_is_ranked_first() -> None:

    ranked = FindingRanker().rank(
        [
            Finding(
                rule="high_memory_usage",
                kind=FindingKind.OBSERVATION,
                severity=Severity.HIGH,
                title="High memory usage",
                description="High memory usage detected",
                resource=ResourceRef(
                    api_version="v1",
                    kind="Pod",
                    namespace="default",
                    name="pod1",
                ),
            ),
            Finding(
                rule="memory_exhaustion",
                kind=FindingKind.DIAGNOSIS,
                severity=Severity.CRITICAL,
                title="Memory exhaustion",
                description="Memory exhaustion detected",
                resource=ResourceRef(
                    api_version="v1",
                    kind="Pod",
                    namespace="default",
                    name="pod1",
                ),
            ),
        ]
    )

    assert ranked[0].rule == "memory_exhaustion"
