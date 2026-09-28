import os
import re
from collections.abc import Callable
from dataclasses import dataclass, replace

import pytest
from openai import Client

from kubesage.ai.providers.openai_compatible import OpenAICompatibleProvider
from kubesage.builders.prompt.prompt_builder import PromptBuilder
from kubesage.models.ai_context import AIContext
from kubesage.models.ai_report import AIReport
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import Finding, FindingKind, ResourceRef, Severity
from kubesage.models.incident_intelligence import IncidentIntelligence
from kubesage.models.timeline import TimelineEvent, TimelineEventSource
from kubesage.utils.config import settings
from tests.ai.scenarios import ReportQualityScenario
from tests.ai.scenarios.ambiguous_resource_pressure import (
    ambiguous_resource_pressure_scenario,
)
from tests.ai.scenarios.application_error import application_error_scenario
from tests.ai.scenarios.contradictory_signals import contradictory_signals_scenario
from tests.ai.scenarios.correlated_but_not_causal import (
    correlated_but_not_causal_scenario,
)
from tests.ai.scenarios.correlated_oom import correlated_oom_scenario
from tests.ai.scenarios.cpu_throttling import cpu_throttling_scenario
from tests.ai.scenarios.crashloop_unknown import crashloop_unknown_scenario
from tests.ai.scenarios.oomkilled import oomkilled_scenario
from tests.ai.scenarios.readiness_failure import readiness_failure_scenario

SCENARIOS = (
    crashloop_unknown_scenario,
    oomkilled_scenario,
    cpu_throttling_scenario,
    readiness_failure_scenario,
    application_error_scenario,
    correlated_oom_scenario,
    ambiguous_resource_pressure_scenario,
    contradictory_signals_scenario,
    correlated_but_not_causal_scenario,
)


UNCERTAINTY_KEYWORDS = (
    "unknown",
    "unconfirmed",
    "unclear",
    "uncertain",
    "no diagnosed cause",
    "without a diagnosed cause",
    "no termination reason",
    "termination reason is not available",
    "not confirmed",
    "cannot be confirmed",
    "not explicitly confirmed",
    "cannot be determined",
    "cannot determine",
    "unable to determine",
    "insufficient evidence",
    "insufficient information",
    "no clear root cause",
    "no concrete",
    "not enough evidence",
    "not enough information",
    "could be",
    "may be",
    "might be",
    "possibly",
    "possible",
    "likely",
    "appears to",
    "appears",
    "suggests",
)


RECOMMENDATION_INVESTIGATION_KEYWORDS = (
    "investigate",
    "investigat",
    "analyze",
    "analyse",
    "examine",
    "check",
    "review",
    "inspect",
    "verify",
    "collect",
    "look into",
)


# Some technical diagnoses are semantically equivalent to the expected
# natural-language keyword. The AI should preserve the technical diagnosis
# rather than being forced to repeat a particular English word.
ROOT_CAUSE_KEYWORD_ALIASES: dict[str, tuple[str, ...]] = {
    "memory": (
        "memory",
        "oom",
        "oomkilled",
        "out of memory",
    ),
    "cpu": (
        "cpu",
        "cpu throttling",
        "cpu throttled",
        "throttling",
    ),
    "restart": (
        "restart",
        "restarted",
        "restarting",
    ),
    "error": (
        "error",
        "exception",
        "failure",
        "failed",
    ),
    "http": (
        "http",
        "status",
    ),
}


def _forbidden_root_cause_is_asserted(root_cause: str, keyword: str) -> bool:
    normalized_keyword = keyword.lower()
    keyword_tokens = normalized_keyword.split()
    keyword_pattern = (
        r"\b"
        + r"(?:\W+\w+){0,2}\W+".join(re.escape(token) for token in keyword_tokens)
        + r"\b"
    )
    normalized_root_cause = re.sub(r"\be\.g\.", "eg", root_cause.lower())
    clauses = re.split(r"[.;]|\bbut\b|\bhowever\b", normalized_root_cause)

    negation_markers = (
        "no ",
        "not ",
        "without ",
        "unknown",
        "unconfirmed",
        "not confirmed",
        "not identified",
        "not reported",
        "not available",
        "not present",
        "not supported",
        "not established",
        "no evidence",
        "no concrete",
        "possible",
        "possibly",
        "potential",
        "hypothesis",
        "may cause",
        "might cause",
        "could cause",
    )

    for clause in clauses:
        if not re.search(keyword_pattern, clause):
            continue

        if any(marker in clause for marker in negation_markers):
            continue

        return True

    return False


def _root_cause_contains_expected_keyword(
    root_cause: str,
    keyword: str,
) -> bool:
    normalized_root_cause = root_cause.lower()
    normalized_keyword = keyword.lower()

    if normalized_keyword in normalized_root_cause:
        return True

    aliases = ROOT_CAUSE_KEYWORD_ALIASES.get(normalized_keyword, ())

    return any(alias in normalized_root_cause for alias in aliases)


@dataclass(frozen=True)
class AIQualityScore:
    root_cause: float
    evidence: float
    recommendations: float
    confidence: float
    completeness: float

    @property
    def overall(self) -> float:
        return sum(
            (
                self.root_cause,
                self.evidence,
                self.recommendations,
                self.confidence,
                self.completeness,
            )
        )


def _keyword_coverage(text: str, keywords: tuple[str, ...]) -> float:
    if not keywords:
        return 1.0

    normalized = text.lower()
    matched = 0

    for keyword in keywords:
        if keyword.lower() in normalized:
            matched += 1
            continue

        aliases = ROOT_CAUSE_KEYWORD_ALIASES.get(keyword.lower(), ())
        if any(alias in normalized for alias in aliases):
            matched += 1

    return matched / len(keywords)


def _recommendation_coverage(
    recommendations: str,
    keywords: tuple[str, ...],
) -> float:
    if not keywords:
        return 1.0

    matched = sum(
        _recommendations_contain_investigation(recommendations)
        if keyword == "__investigation__"
        else keyword.lower() in recommendations.lower()
        for keyword in keywords
    )
    return matched / len(keywords)


def _confidence_score(report: AIReport, scenario: ReportQualityScenario) -> float:
    if report.confidence is None:
        return 0.0

    if scenario.require_uncertainty:
        return max(0.0, 1.0 - report.confidence)

    return min(1.0, report.confidence)


def _report_expresses_uncertainty(report: AIReport) -> bool:
    root_cause = (report.root_cause or "").strip().lower()
    return (
        report.root_cause is None
        or any(keyword in root_cause for keyword in UNCERTAINTY_KEYWORDS)
        or (report.confidence is not None and report.confidence <= 0.7)
    )


def _normalize_evidence_source(source: str | None) -> str:
    if source is None:
        return ""

    return source.strip().lower()


def score_report_quality(
    report: AIReport,
    scenario: ReportQualityScenario,
) -> AIQualityScore:
    root_cause = (report.root_cause or "").strip()
    evidence_descriptions = " ".join(
        evidence.description or "" for evidence in report.evidence
    )
    recommendations = " ".join(report.recommendations)

    completeness_fields = (
        bool(report.summary),
        bool(root_cause) if scenario.require_root_cause else True,
        bool(report.evidence),
        bool(report.recommendations),
        bool(report.impact),
    )

    return AIQualityScore(
        root_cause=30.0
        * _keyword_coverage(
            root_cause,
            scenario.expected_root_cause_keywords,
        ),
        evidence=25.0
        * _keyword_coverage(
            evidence_descriptions,
            scenario.required_evidence_keywords,
        ),
        recommendations=20.0
        * _recommendation_coverage(
            recommendations,
            scenario.required_recommendation_keywords,
        ),
        confidence=10.0 * _confidence_score(report, scenario),
        completeness=15.0 * (sum(completeness_fields) / len(completeness_fields)),
    )


def build_prompt(scenario: ReportQualityScenario) -> str:
    intelligence = IncidentIntelligence(
        findings=scenario.findings,
        root_causes=[],
        correlations=[],
        timeline=scenario.timeline,
    )
    context = AIContext(
        incident=scenario.incident,
        intelligence=intelligence,
    )

    return PromptBuilder().build(context)


def _scenario_evidence_by_id(
    scenario: ReportQualityScenario,
) -> dict[str, tuple[Finding, Evidence]]:
    return {
        evidence.id: (finding, evidence)
        for finding in scenario.findings
        for evidence in finding.structured_evidences
    }


def _canonical_finding_rule(
    reported_rule: str,
    scenario: ReportQualityScenario,
) -> str | None:
    normalized = reported_rule.strip().casefold()
    for finding in scenario.findings:
        if normalized in {finding.rule.casefold(), finding.title.casefold()}:
            return finding.rule
    return None


def _timeline_event_matches_evidence(
    evidence: Evidence,
    event: TimelineEvent,
) -> bool:
    if evidence.source == "prometheus":
        return event.source == TimelineEventSource.PROMETHEUS

    if evidence.source == "kubernetes":
        return event.source == TimelineEventSource.KUBERNETES

    if evidence.source in {"loki", "log"}:
        return event.source == TimelineEventSource.LOKI

    if evidence.source == "event":
        return event.source == TimelineEventSource.KUBERNETES

    return False


def _assert_report_evidence_attribution(
    report: AIReport,
    scenario: ReportQualityScenario,
) -> None:
    evidence_by_id = _scenario_evidence_by_id(scenario)

    assert evidence_by_id, f"{scenario.name}: expected canonical evidence"

    assert report.evidence, (
        f"{scenario.name}: AI report must contain at least one evidence reference"
    )

    referenced_ids = [evidence.id for evidence in report.evidence]

    assert len(referenced_ids) == len(set(referenced_ids)), (
        f"{scenario.name}: AI report contains duplicate evidence IDs: "
        f"{referenced_ids!r}"
    )

    for evidence in report.evidence:
        assert evidence.id in evidence_by_id, (
            f"{scenario.name}: LLM referenced unknown evidence ID {evidence.id!r}"
        )

        finding, canonical_evidence = evidence_by_id[evidence.id]

        assert canonical_evidence.id == evidence.id

        assert evidence.source == canonical_evidence.source, (
            f"{scenario.name}: evidence {evidence.id!r} has incorrect "
            f"source {evidence.source!r}; expected "
            f"{canonical_evidence.source!r}"
        )

        assert evidence.description, (
            f"{scenario.name}: evidence {evidence.id!r} must have a description"
        )

        assert _normalize_evidence_source(
            evidence.source
        ) == _normalize_evidence_source(canonical_evidence.source), (
            f"{scenario.name}: evidence {evidence.id!r} has incorrect "
            f"source {evidence.source!r}; expected "
            f"{canonical_evidence.source!r}"
        )

        assert finding.structured_evidences, (
            f"{scenario.name}: finding {finding.title!r} has no structured evidence"
        )


def _assert_report_evidence_ids_are_known(
    report: AIReport,
    scenario: ReportQualityScenario,
) -> None:
    valid_evidence_ids = set(_scenario_evidence_by_id(scenario))

    for evidence in report.evidence:
        assert evidence.id in valid_evidence_ids, (
            f"{scenario.name}: unknown evidence ID {evidence.id!r}"
        )


def _assert_report_evidence_sources_match_scenario(
    report: AIReport,
    scenario: ReportQualityScenario,
) -> None:
    evidence_by_id = _scenario_evidence_by_id(scenario)

    for evidence in report.evidence:
        assert evidence.id in evidence_by_id

        _, canonical_evidence = evidence_by_id[evidence.id]

        assert evidence.source == canonical_evidence.source, (
            f"{scenario.name}: evidence {evidence.id!r} source mismatch: "
            f"got {evidence.source!r}, "
            f"expected {canonical_evidence.source!r}"
        )


def _assert_report_evidence_ids_are_unique(
    report: AIReport,
    scenario: ReportQualityScenario,
) -> None:
    evidence_ids = [evidence.id for evidence in report.evidence]

    assert len(evidence_ids) == len(set(evidence_ids)), (
        f"{scenario.name}: duplicate evidence IDs in AI report: {evidence_ids!r}"
    )


def _assert_report_evidence_timeline_consistency(
    report: AIReport,
    scenario: ReportQualityScenario,
) -> None:
    if not scenario.timeline:
        return

    evidence_by_id = _scenario_evidence_by_id(scenario)

    for evidence in report.evidence:
        canonical_evidence = evidence_by_id[evidence.id][1]

        matching_events = [
            event
            for event in scenario.timeline
            if _timeline_event_matches_evidence(
                canonical_evidence,
                event,
            )
        ]

        assert matching_events, (
            f"{scenario.name}: evidence {evidence.id!r} has no matching timeline source"
        )


def _recommendations_contain_investigation(
    recommendations: str,
) -> bool:
    return any(
        keyword in recommendations for keyword in RECOMMENDATION_INVESTIGATION_KEYWORDS
    )


def assert_report_quality(
    report: AIReport,
    scenario: ReportQualityScenario,
) -> AIQualityScore:
    assert report.summary

    assert report.summary != "AI analysis could not be completed.", (
        f"{scenario.name}: AI provider did not return a report"
    )
    assert report.status.value == "success", (
        f"{scenario.name}: generated report must have success status, "
        f"got {report.status.value!r}"
    )

    reported_finding_rules = [finding.rule for finding in report.findings]
    assert len(reported_finding_rules) == len(set(reported_finding_rules)), (
        f"{scenario.name}: duplicate finding references in report"
    )
    canonical_reported_rules = [
        _canonical_finding_rule(rule, scenario) for rule in reported_finding_rules
    ]
    assert all(rule is not None for rule in canonical_reported_rules), (
        f"{scenario.name}: report references findings absent from context: "
        f"{reported_finding_rules!r}"
    )
    missing_finding_rules = set(scenario.required_finding_rules) - set(
        canonical_reported_rules
    )
    assert not missing_finding_rules, (
        f"{scenario.name}: missing relevant finding references "
        f"{sorted(missing_finding_rules)!r}"
    )

    root_cause = (report.root_cause or "").strip().lower()
    recommendations = " ".join(report.recommendations).lower()

    if scenario.require_root_cause:
        assert root_cause, f"{scenario.name}: expected a root cause"

        assert not any(keyword in root_cause for keyword in UNCERTAINTY_KEYWORDS), (
            f"{scenario.name}: expected a concrete root cause, "
            f"got uncertain root cause={report.root_cause!r}"
        )

    if scenario.require_uncertainty:
        assert _report_expresses_uncertainty(report), (
            f"{scenario.name}: expected uncertainty, "
            f"got root cause={report.root_cause!r}, "
            f"confidence={report.confidence!r}"
        )
        assert report.confidence is not None and report.confidence <= 0.7, (
            f"{scenario.name}: uncertain diagnosis must have confidence <= 0.7, "
            f"got {report.confidence!r}"
        )

    for keyword in scenario.expected_root_cause_keywords:
        assert _root_cause_contains_expected_keyword(
            root_cause,
            keyword,
        ), (
            f"{scenario.name}: expected {keyword!r} "
            f"in root cause, got {report.root_cause!r}"
        )

    for keyword in scenario.forbidden_root_cause_keywords:
        assert not _forbidden_root_cause_is_asserted(
            root_cause,
            keyword,
        ), (
            f"{scenario.name}: forbidden root-cause claim "
            f"{keyword!r}, got {report.root_cause!r}"
        )

    for keyword in scenario.required_recommendation_keywords:
        if keyword == "__investigation__":
            assert _recommendations_contain_investigation(recommendations), (
                f"{scenario.name}: expected investigation-oriented "
                f"recommendations, got {report.recommendations!r}"
            )
            continue

        assert keyword.lower() in recommendations, (
            f"{scenario.name}: expected {keyword!r} "
            f"in recommendations, got {report.recommendations!r}"
        )

    _assert_report_evidence_attribution(report, scenario)
    _assert_report_evidence_ids_are_known(report, scenario)
    _assert_report_evidence_sources_match_scenario(report, scenario)
    _assert_report_evidence_ids_are_unique(report, scenario)
    _assert_report_evidence_timeline_consistency(report, scenario)

    score = score_report_quality(report, scenario)
    assert score.overall >= 80.0, (
        f"{scenario.name}: quality score {score.overall:.1f}/100 is below 80"
    )
    return score


@pytest.mark.parametrize(
    "scenario_factory",
    [*SCENARIOS],
    ids=lambda factory: factory().name,
)
def test_report_quality_scenario_builds_valid_context(
    scenario_factory: Callable[[], ReportQualityScenario],
) -> None:
    scenario = scenario_factory()

    intelligence = IncidentIntelligence(
        findings=scenario.findings,
        root_causes=[],
        correlations=[],
        timeline=scenario.timeline,
    )
    context = AIContext(incident=scenario.incident, intelligence=intelligence)

    assert context.finding_count == len(scenario.findings)
    assert context.has_findings

    prompt = PromptBuilder().build(context)
    assert scenario.incident.pod in prompt

    for evidence in scenario.required_evidence_keywords:
        assert evidence.lower() in prompt.lower()


@pytest.mark.ai_quality
@pytest.mark.skipif(
    os.getenv("KUBESAGE_RUN_AI_QUALITY") != "1",
    reason="AI quality tests require an explicit live AI provider",
)
@pytest.mark.parametrize(
    "scenario_factory",
    [*SCENARIOS],
    ids=lambda factory: factory().name,
)
def test_ai_report_quality(
    scenario_factory: Callable[[], ReportQualityScenario],
) -> None:
    scenario = scenario_factory()
    client = Client(base_url=settings.ai_url, api_key=settings.ai_api_key)
    provider = OpenAICompatibleProvider(client=client, model=settings.ai_model)

    report = provider.analyze(build_prompt(scenario))

    print(f"\n{'=' * 80}")
    print(f"SCENARIO: {scenario.name}")
    print(f"{'=' * 80}")
    print(report.model_dump_json(indent=2))

    score = assert_report_quality(report, scenario)

    print(
        "QUALITY SCORE: "
        f"{score.overall:.1f}/100 "
        f"(root={score.root_cause:.1f}, "
        f"evidence={score.evidence:.1f}, "
        f"recommendations={score.recommendations:.1f}, "
        f"confidence={score.confidence:.1f}, "
        f"completeness={score.completeness:.1f})"
    )


@pytest.mark.ai_quality
@pytest.mark.skipif(
    os.getenv("KUBESAGE_RUN_AI_QUALITY") != "1",
    reason="AI quality tests require an explicit live AI provider",
)
def test_irrelevant_duplicate_evidence_does_not_change_diagnosis() -> None:
    scenario = oomkilled_scenario()
    unrelated = Finding(
        rule="unrelated_network_observation",
        kind=FindingKind.OBSERVATION,
        severity=Severity.INFO,
        confidence=0.99,
        title="Unrelated worker network activity",
        description="A separate metrics worker has normal network activity.",
        resource=ResourceRef(
            api_version="v1",
            kind="Pod",
            namespace="monitoring",
            name="metrics-worker",
        ),
        structured_evidences=[
            Evidence(
                name="network_activity",
                value="1",
                unit="connection",
                source="prometheus",
                type=EvidenceType.METRIC,
                description=(
                    "An unrelated metrics worker recorded one network connection."
                ),
            ),
        ],
    )
    noisy_scenario = replace(
        scenario,
        findings=[*scenario.findings, unrelated, unrelated.model_copy(deep=True)],
    )
    client = Client(base_url=settings.ai_url, api_key=settings.ai_api_key)
    provider = OpenAICompatibleProvider(client=client, model=settings.ai_model)

    baseline_report = provider.analyze(build_prompt(scenario))
    noisy_report = provider.analyze(build_prompt(noisy_scenario))

    assert_report_quality(baseline_report, scenario)
    assert_report_quality(noisy_report, scenario)
    assert baseline_report.confidence is not None
    assert noisy_report.confidence is not None
    assert abs(baseline_report.confidence - noisy_report.confidence) <= 0.2, (
        "irrelevant duplicated evidence changed confidence by more than 0.2: "
        f"{baseline_report.confidence} -> {noisy_report.confidence}"
    )


def test_evidence_ids_are_unique_in_scenario() -> None:
    for scenario_factory in SCENARIOS:
        scenario = scenario_factory()

        evidence_ids = [
            evidence.id
            for finding in scenario.findings
            for evidence in finding.structured_evidences
        ]

        assert evidence_ids, f"{scenario.name}: expected evidence"

        assert len(evidence_ids) == len(set(evidence_ids)), (
            f"{scenario.name}: evidence IDs must be unique"
        )


def test_evidence_ids_are_attributable_to_findings() -> None:
    for scenario_factory in SCENARIOS:
        scenario = scenario_factory()

        evidence_by_id = _scenario_evidence_by_id(scenario)

        assert evidence_by_id, f"{scenario.name}: expected evidence"

        for evidence_id, (
            finding,
            evidence,
        ) in evidence_by_id.items():
            assert evidence.id == evidence_id
            assert evidence in finding.structured_evidences


@pytest.mark.ai_quality
@pytest.mark.skipif(
    os.getenv("KUBESAGE_RUN_AI_QUALITY") != "1",
    reason="AI quality tests require an explicit live AI provider",
)
def test_ai_report_evidence_ids_match_scenario() -> None:
    scenario = oomkilled_scenario()
    client = Client(base_url=settings.ai_url, api_key=settings.ai_api_key)
    provider = OpenAICompatibleProvider(client=client, model=settings.ai_model)

    report = provider.analyze(build_prompt(scenario))

    _assert_report_evidence_ids_are_known(report, scenario)


@pytest.mark.ai_quality
@pytest.mark.skipif(
    os.getenv("KUBESAGE_RUN_AI_QUALITY") != "1",
    reason="AI quality tests require an explicit live AI provider",
)
def test_ai_report_evidence_sources_match_scenario() -> None:
    scenario = oomkilled_scenario()
    client = Client(base_url=settings.ai_url, api_key=settings.ai_api_key)
    provider = OpenAICompatibleProvider(client=client, model=settings.ai_model)

    report = provider.analyze(build_prompt(scenario))

    _assert_report_evidence_sources_match_scenario(report, scenario)


@pytest.mark.ai_quality
@pytest.mark.skipif(
    os.getenv("KUBESAGE_RUN_AI_QUALITY") != "1",
    reason="AI quality tests require an explicit live AI provider",
)
def test_ai_report_evidence_ids_are_unique() -> None:
    scenario = crashloop_unknown_scenario()
    client = Client(base_url=settings.ai_url, api_key=settings.ai_api_key)
    provider = OpenAICompatibleProvider(client=client, model=settings.ai_model)

    report = provider.analyze(build_prompt(scenario))

    _assert_report_evidence_ids_are_unique(report, scenario)


def test_evidence_attribution_is_consistent() -> None:
    for scenario_factory in SCENARIOS:
        scenario = scenario_factory()

        evidence_by_id = _scenario_evidence_by_id(scenario)

        assert evidence_by_id, f"{scenario.name}: expected evidence"

        for evidence_id, (_finding, evidence) in evidence_by_id.items():
            assert evidence.id == evidence_id
            assert evidence.source

            if scenario.timeline:
                matching_events = [
                    event
                    for event in scenario.timeline
                    if _timeline_event_matches_evidence(
                        evidence,
                        event,
                    )
                ]

                assert matching_events, (
                    f"{scenario.name}: evidence "
                    f"{evidence.id!r} has no matching "
                    "timeline source"
                )


def test_evidence_timeline_consistency() -> None:
    for scenario_factory in SCENARIOS:
        scenario = scenario_factory()

        if not scenario.timeline:
            continue

        evidence_by_id = _scenario_evidence_by_id(scenario)
        for evidence_id, (_finding, evidence) in evidence_by_id.items():
            matching_events = [
                event
                for event in scenario.timeline
                if _timeline_event_matches_evidence(evidence, event)
            ]

            assert matching_events, (
                f"{scenario.name}: evidence "
                f"{evidence_id!r} has no matching "
                "timeline event"
            )


@pytest.mark.parametrize(
    ("root_cause", "confidence", "expected"),
    [
        ("Unconfirmed root cause", 0.9, True),
        ("No termination reason is available", 0.9, True),
        ("Root cause cannot be confirmed", 0.9, True),
        ("HTTP 500 followed by a restart", 0.7, True),
        ("HTTP 500 followed by a restart", 0.71, False),
        ("OOMKilled", 0.95, False),
    ],
)
def test_uncertainty_detection_handles_wording_and_confidence(
    root_cause: str,
    confidence: float,
    expected: bool,
) -> None:
    report = AIReport(
        summary="Incident summary",
        root_cause=root_cause,
        confidence=confidence,
    )

    assert _report_expresses_uncertainty(report) is expected


@pytest.mark.parametrize(
    ("root_cause", "keyword", "asserted"),
    [
        ("CPU usage caused the HTTP 500 error", "cpu caused", True),
        ("There is no evidence CPU caused the HTTP 500", "cpu caused", False),
        ("CPU did not cause the HTTP 500", "cpu caused", False),
        ("OOMKilled is not confirmed (e.g. no termination reason)", "oomkilled", False),
        (
            "Possible causes include memory pressure or CPU throttling",
            "cpu throttling",
            False,
        ),
    ],
)
def test_forbidden_root_cause_detection_respects_negation(
    root_cause: str,
    keyword: str,
    asserted: bool,
) -> None:
    assert _forbidden_root_cause_is_asserted(root_cause, keyword) is asserted
