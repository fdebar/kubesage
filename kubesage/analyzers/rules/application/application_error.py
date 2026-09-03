from collections import OrderedDict
from dataclasses import dataclass

from kubesage.analyzers.application_error import (
    ApplicationErrorClassification,
    ApplicationErrorClassifier,
)
from kubesage.analyzers.rules.base import BaseRule
from kubesage.models.application_error import (
    ApplicationErrorGroup,
    ApplicationErrorKind,
)
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import Finding, FindingKind, Severity
from kubesage.models.incident import Incident


@dataclass
class _MutableApplicationErrorGroup:
    fingerprint: str
    classification: ApplicationErrorClassification
    occurrences: int
    first_seen: str
    last_seen: str
    example_messages: list[str]
    labels: dict[str, str]


class ApplicationErrorRule(BaseRule):
    rule_id = "application_error"
    title = "Detect application errors"
    description = "Detect application errors reported in application logs."

    classifier = ApplicationErrorClassifier()

    MAX_EXAMPLES = 3

    def evaluate(self, incident: Incident) -> list[Finding]:
        if not incident.loki_logs:
            return []

        groups: OrderedDict[str, _MutableApplicationErrorGroup] = OrderedDict()

        for entry in incident.loki_logs.entries:
            classification = self.classifier.classify(entry.message)

            if classification is None:
                continue

            fingerprint = self.classifier.fingerprint(
                classification,
                entry.message,
            )

            timestamp = entry.timestamp.isoformat()

            group = groups.get(fingerprint)

            if group is None:
                groups[fingerprint] = _MutableApplicationErrorGroup(
                    fingerprint=fingerprint,
                    classification=classification,
                    occurrences=1,
                    first_seen=timestamp,
                    last_seen=timestamp,
                    example_messages=[entry.message],
                    labels=dict(entry.labels),
                )
                continue

            group.occurrences += 1

            if timestamp < group.first_seen:
                group.first_seen = timestamp

            if timestamp > group.last_seen:
                group.last_seen = timestamp

            if (
                entry.message not in group.example_messages
                and len(group.example_messages) < self.MAX_EXAMPLES
            ):
                group.example_messages.append(entry.message)

            if not group.labels:
                group.labels = dict(entry.labels)

        return [
            self._build_finding(incident, self._to_group(group))
            for group in groups.values()
        ]

    def _to_group(
        self,
        group: _MutableApplicationErrorGroup,
    ) -> ApplicationErrorGroup:
        return ApplicationErrorGroup(
            fingerprint=group.fingerprint,
            kind=group.classification.kind,
            domain=(
                group.classification.domain.value
                if group.classification.domain
                else None
            ),
            occurrences=group.occurrences,
            first_seen=group.first_seen,
            last_seen=group.last_seen,
            example_messages=group.example_messages,
            labels=group.labels,
        )

    def _build_finding(
        self,
        incident: Incident,
        group: ApplicationErrorGroup,
    ) -> Finding:
        title = self._title(group)

        description = self._description(group)

        evidence_metadata = {
            "error_kind": group.kind.value,
            "fingerprint": group.fingerprint,
            "occurrences": group.occurrences,
            "first_seen": group.first_seen,
            "last_seen": group.last_seen,
            "examples": group.example_messages,
            "labels": group.labels,
        }

        if group.domain:
            evidence_metadata["error_domain"] = group.domain

        finding_metadata = {
            "error_kind": group.kind.value,
            "fingerprint": group.fingerprint,
            "occurrences": group.occurrences,
            "first_seen": group.first_seen,
            "last_seen": group.last_seen,
        }

        if group.domain:
            finding_metadata["error_domain"] = group.domain

        evidence = Evidence(
            type=EvidenceType.LOG,
            name="application_error",
            value=group.example_messages[0],
            source="loki",
            description=(
                f"{group.occurrences} occurrence"
                f"{'' if group.occurrences == 1 else 's'} observed "
                f"between {group.first_seen} and {group.last_seen}."
            ),
            metadata=evidence_metadata,
        )

        return Finding(
            rule=self.rule_id,
            severity=Severity.ERROR,
            kind=FindingKind.OBSERVATION,
            title=title,
            description=description,
            metadata=finding_metadata,
            resource=self._pod_resource(incident),
            structured_evidences=[evidence],
            confidence=0.90,
            priority=30,
        )

    def _title(self, group: ApplicationErrorGroup) -> str:
        if group.domain == "database":
            database_titles = {
                ApplicationErrorKind.CONNECTION_ERROR: ("Database connection failure"),
                ApplicationErrorKind.TIMEOUT: "Database timeout",
                ApplicationErrorKind.HTTP_5XX: "Database HTTP 5xx error",
                ApplicationErrorKind.EXCEPTION: "Database exception",
                ApplicationErrorKind.GENERIC_ERROR: "Database error",
            }

            return database_titles[group.kind]

        titles = {
            ApplicationErrorKind.CONNECTION_ERROR: ("Application connection failure"),
            ApplicationErrorKind.TIMEOUT: "Application timeout",
            ApplicationErrorKind.HTTP_5XX: "HTTP 5xx error",
            ApplicationErrorKind.EXCEPTION: "Application exception",
            ApplicationErrorKind.GENERIC_ERROR: "Application error",
        }

        return titles[group.kind]

    def _description(self, group: ApplicationErrorGroup) -> str:
        if group.domain == "database":
            descriptions = {
                ApplicationErrorKind.CONNECTION_ERROR: (
                    "Application logs report a database connection failure."
                ),
                ApplicationErrorKind.TIMEOUT: (
                    "Application logs report a database timeout."
                ),
                ApplicationErrorKind.HTTP_5XX: (
                    "Application logs report a database-related HTTP 5xx error."
                ),
                ApplicationErrorKind.EXCEPTION: (
                    "Application logs report a database-related exception."
                ),
                ApplicationErrorKind.GENERIC_ERROR: (
                    "Application logs report a database error."
                ),
            }
        else:
            descriptions = {
                ApplicationErrorKind.CONNECTION_ERROR: (
                    "Application logs report a connection failure."
                ),
                ApplicationErrorKind.TIMEOUT: ("Application logs report a timeout."),
                ApplicationErrorKind.HTTP_5XX: (
                    "Application logs report an HTTP 5xx server error."
                ),
                ApplicationErrorKind.EXCEPTION: (
                    "Application logs report an exception or traceback."
                ),
                ApplicationErrorKind.GENERIC_ERROR: (
                    "Application logs report an application error."
                ),
            }

        occurrence = "occurrence" if group.occurrences == 1 else "occurrences"

        return (
            f"{descriptions[group.kind]} "
            f"{group.occurrences} {occurrence} observed "
            f"between {group.first_seen} and {group.last_seen}."
        )
