import structlog

from kubesage.builders.timeline import TimelineBuilder
from kubesage.models.finding import Finding, FindingKind
from kubesage.models.incident import Incident
from kubesage.models.incident_intelligence import (
    Correlation,
    CorrelationType,
    IncidentIntelligence,
    RootCauseCandidate,
)

logger = structlog.get_logger()


class IncidentIntelligenceBuilder:
    """Build structured intelligence from an incident and its findings."""

    def __init__(self, timeline_builder: TimelineBuilder | None = None) -> None:
        self.timeline_builder = timeline_builder or TimelineBuilder()

    def build(
        self,
        incident: Incident,
        findings: list[Finding],
    ) -> IncidentIntelligence:
        logger.info(
            "incident_intelligence_building_started",
            namespace=incident.namespace,
            pod=incident.pod,
        )

        timeline = self.timeline_builder.build(incident)
        correlations = self._build_correlations(findings)
        root_causes = self._build_root_causes(findings)

        logger.info(
            "incident_intelligence_building_completed",
            namespace=incident.namespace,
            pod=incident.pod,
            findings_count=len(findings),
            timeline_events_count=len(timeline),
            correlations_count=len(correlations),
            root_causes_count=len(root_causes),
            supporting_evidence_count=sum(
                len(candidate.supporting_evidence) for candidate in root_causes
            ),
        )

        return IncidentIntelligence(
            findings=findings,
            timeline=timeline,
            correlations=correlations,
            root_causes=root_causes,
        )

    def _build_correlations(self, findings: list[Finding]) -> list[Correlation]:
        correlations: list[Correlation] = []
        seen: set[tuple[str, str, CorrelationType]] = set()

        for finding in findings:
            for caused_by in finding.caused_by:
                key = (finding.rule, caused_by, CorrelationType.CAUSED_BY)
                if key in seen:
                    continue
                seen.add(key)

                correlations.append(
                    Correlation(
                        source_finding=finding.rule,
                        target_finding=caused_by,
                        type=CorrelationType.CAUSED_BY,
                    )
                )

            for related in finding.related_findings:
                key = (finding.rule, related, CorrelationType.RELATED)
                if key in seen:
                    continue
                seen.add(key)

                correlations.append(
                    Correlation(
                        source_finding=finding.rule,
                        target_finding=related,
                        type=CorrelationType.RELATED,
                    )
                )

        return correlations

    def _build_root_causes(self, findings: list[Finding]) -> list[RootCauseCandidate]:
        candidates: list[RootCauseCandidate] = []

        finding_by_rule = {finding.rule: finding for finding in findings}
        for finding in findings:
            if finding.kind != FindingKind.DIAGNOSIS:
                continue

            if not finding.caused_by:
                continue

            supporting_evidence: list[str] = []
            seen_evidence: set[str] = set()

            for supporting_rule in finding.caused_by:
                supporting_finding = finding_by_rule.get(supporting_rule)

                if supporting_finding is None:
                    continue

                for evidence in supporting_finding.structured_evidences:
                    if evidence.id in seen_evidence:
                        continue

                    seen_evidence.add(evidence.id)
                    supporting_evidence.append(evidence.id)

            candidates.append(
                RootCauseCandidate(
                    finding=finding.rule,
                    title=finding.title,
                    description=finding.description,
                    confidence=finding.confidence,
                    supporting_findings=list(finding.caused_by),
                    supporting_evidence=supporting_evidence,
                )
            )

        return candidates
