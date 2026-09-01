import os
from dataclasses import dataclass

import pytest
from openai import Client

from kubesage.ai.providers.openai_compatible import OpenAICompatibleProvider
from kubesage.builders.prompt.prompt_builder import PromptBuilder
from kubesage.models.ai_context import AIContext
from kubesage.models.ai_report import AIReport
from kubesage.utils.config import settings
from tests.ai.scenarios import ReportQualityScenario
from tests.ai.scenarios.application_error import application_error_scenario
from tests.ai.scenarios.correlated_oom import correlated_oom_scenario
from tests.ai.scenarios.cpu_throttling import cpu_throttling_scenario
from tests.ai.scenarios.crashloop_unknown import crashloop_unknown_scenario
from tests.ai.scenarios.oomkilled import oomkilled_scenario
from tests.ai.scenarios.readiness_failure import readiness_failure_scenario

UNCERTAINTY_KEYWORDS = (
    "unknown",
    "uncertain",
    "unclear",
    "undetermined",
    "cannot be determined",
    "unable to determine",
    "not determined",
    "no specific",
    "not known",
    "insufficient evidence",
    "insufficient information",
    "no evidence",
    "not enough evidence",
    "cannot identify",
    "unable to identify",
)


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
    matched = sum(keyword.lower() in normalized for keyword in keywords)

    return matched / len(keywords)


def _confidence_score(report: AIReport, scenario: ReportQualityScenario) -> float:
    if report.confidence is None:
        return 0.0

    if scenario.require_uncertainty:
        return max(0.0, 1.0 - report.confidence)

    return min(1.0, report.confidence)


def score_report_quality(
    report: AIReport,
    scenario: ReportQualityScenario,
) -> AIQualityScore:
    root_cause = (report.root_cause or "").strip()
    evidences_ids = " ".join(r.description or "" for r in report.evidence)
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
        * _keyword_coverage(root_cause, scenario.expected_root_cause_keywords),
        evidence=25.0
        * _keyword_coverage(evidences_ids, scenario.required_evidence_keywords),
        recommendations=20.0
        * _keyword_coverage(recommendations, scenario.required_recommendation_keywords),
        confidence=10.0 * _confidence_score(report, scenario),
        completeness=15.0 * (sum(completeness_fields) / len(completeness_fields)),
    )


def build_prompt(scenario: ReportQualityScenario) -> str:
    context = AIContext(
        incident=scenario.incident,
        findings=scenario.findings,
        timeline=scenario.timeline,
    )

    return PromptBuilder().build(context)


def assert_report_quality(
    report: AIReport,
    scenario: ReportQualityScenario,
) -> AIQualityScore:
    assert report.summary
    assert report.summary != "AI analysis could not be completed.", (
        f"{scenario.name}: AI provider did not return a report"
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
        uncertainty_detected = (
            report.root_cause is None
            or any(keyword in root_cause for keyword in UNCERTAINTY_KEYWORDS)
            or (report.confidence is not None and report.confidence < 0.7)
        )

        assert uncertainty_detected, (
            f"{scenario.name}: expected uncertainty, "
            f"got root cause={report.root_cause!r}, "
            f"confidence={report.confidence!r}"
        )

    for keyword in scenario.expected_root_cause_keywords:
        assert keyword.lower() in root_cause, (
            f"{scenario.name}: expected {keyword!r} "
            f"in root cause, got {report.root_cause!r}"
        )

    for keyword in scenario.forbidden_root_cause_keywords:
        assert keyword.lower() not in root_cause, (
            f"{scenario.name}: forbidden {keyword!r} "
            f"in root cause, got {report.root_cause!r}"
        )

    for keyword in scenario.required_recommendation_keywords:
        assert keyword.lower() in recommendations, (
            f"{scenario.name}: expected {keyword!r} "
            f"in recommendations, got {report.recommendations!r}"
        )

    valid_evidence_ids = {
        evidence.id
        for finding in scenario.findings
        for evidence in finding.structured_evidences
    }

    for evidence in report.evidence:
        assert evidence.id in valid_evidence_ids

    return score_report_quality(report, scenario)


@pytest.mark.parametrize(
    "scenario",
    [
        crashloop_unknown_scenario(),
        oomkilled_scenario(),
        cpu_throttling_scenario(),
        readiness_failure_scenario(),
        application_error_scenario(),
        correlated_oom_scenario(),
    ],
    ids=lambda scenario: scenario.name,
)
def test_report_quality_scenario_builds_valid_context(
    scenario: ReportQualityScenario,
) -> None:
    context = AIContext(
        incident=scenario.incident,
        findings=scenario.findings,
        timeline=scenario.timeline,
    )

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
    "scenario",
    [
        crashloop_unknown_scenario(),
        oomkilled_scenario(),
        cpu_throttling_scenario(),
        readiness_failure_scenario(),
        application_error_scenario(),
        correlated_oom_scenario(),
    ],
    ids=lambda scenario: scenario.name,
)
def test_ai_report_quality(scenario: ReportQualityScenario) -> None:
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
def test_oomkilled_ai_report_quality() -> None:
    scenario = oomkilled_scenario()
    client = Client(base_url=settings.ai_url, api_key=settings.ai_api_key)
    provider = OpenAICompatibleProvider(client=client, model=settings.ai_model)
    report: AIReport = provider.analyze(build_prompt(scenario))

    print(f"\n{'=' * 80}")
    print("SCENARIO: oomkilled")
    print(f"{'=' * 80}")
    print(report.model_dump_json(indent=2))

    score = assert_report_quality(report, scenario)

    print(f"QUALITY SCORE: {score.overall:.1f}/100")


def test_evidence_ids_are_unique_in_scenario() -> None:
    for scenario in (
        crashloop_unknown_scenario(),
        oomkilled_scenario(),
        cpu_throttling_scenario(),
        readiness_failure_scenario(),
        application_error_scenario(),
        correlated_oom_scenario(),
    ):
        evidence_ids = [
            evidence.id
            for finding in scenario.findings
            for evidence in finding.structured_evidences
        ]

        assert evidence_ids, f"{scenario.name}: expected evidence"
        assert len(evidence_ids) == len(set(evidence_ids)), (
            f"{scenario.name}: evidence IDs must be unique"
        )


def test_ai_report_evidence_ids_match_scenario() -> None:
    scenario = oomkilled_scenario()
    client = Client(base_url=settings.ai_url, api_key=settings.ai_api_key)
    provider = OpenAICompatibleProvider(client=client, model=settings.ai_model)

    report = provider.analyze(build_prompt(scenario))

    valid_evidence_ids = {
        evidence.id
        for finding in scenario.findings
        for evidence in finding.structured_evidences
    }

    assert report.evidence

    for evidence in report.evidence:
        assert evidence.id in valid_evidence_ids, (
            f"{scenario.name}: unknown evidence ID {evidence.id!r}"
        )
