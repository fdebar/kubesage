from datetime import datetime

from kubesage.analyzers.rules.availability.crashloop import CrashLoopRule
from kubesage.analyzers.rules.resources.cpu_throttling import CPUThrottlingRule
from kubesage.analyzers.rules.resources.high_cpu_usage import HighCPUUsageRule
from kubesage.builders.prompt.prompt_builder import PromptBuilder
from kubesage.models.ai_context import AIContext
from kubesage.models.container import (
    ContainerResources,
    ContainerSnapshot,
    ContainerUsage,
)
from kubesage.models.finding import FindingKind, Severity
from kubesage.models.incident import Incident
from kubesage.models.incident_intelligence import IncidentIntelligence
from kubesage.models.log import LogEntry, LogSnapshot
from kubesage.services.findings_correlator import (
    FindingsCorrelator,
)


def build_cpu_contention_incident() -> Incident:
    return Incident(
        namespace="production",
        pod="checkout-api-7f8d9",
        phase="Running",
        observed_at=datetime.now(),
        kubernetes_logs=LogSnapshot(
            source="kubernetes",
            entries=[
                LogEntry(
                    timestamp=datetime.now(),
                    message="request processing latency increased",
                ),
                LogEntry(timestamp=datetime.now(), message="worker CPU usage is high"),
                LogEntry(timestamp=datetime.now(), message="container restarted"),
            ],
        ),
        loki_logs=None,
        containers=[
            ContainerSnapshot(
                name="checkout-api",
                image="checkout:v1",
                ready=False,
                restart_count=12,
                waiting_reason="CrashLoopBackOff",
                last_exit_reason="Error",
                usage=ContainerUsage(
                    name="checkout-api",
                    cpu_usage=0.95,
                    cpu_throttling_ratio=0.35,
                ),
                resources=ContainerResources(name="checkout-api", cpu_limit=1.0),
            ),
        ],
        events=[],
        metrics=None,
        prometheus=None,
    )


def test_full_cpu_diagnostic_pipeline() -> None:
    incident = build_cpu_contention_incident()
    findings = []
    rules = [CrashLoopRule(), HighCPUUsageRule(), CPUThrottlingRule()]

    for rule in rules:
        findings.extend(rule.evaluate(incident))

    assert len(findings) == 3
    assert {finding.rule for finding in findings} == {
        "crashloop",
        "high_cpu_usage",
        "cpu_throttling",
    }

    findings = FindingsCorrelator().correlate(findings)
    diagnosis = next(
        finding for finding in findings if finding.rule == "cpu_contention"
    )

    assert diagnosis.kind == FindingKind.DIAGNOSIS
    assert diagnosis.severity == Severity.HIGH
    assert diagnosis.caused_by == ["high_cpu_usage", "cpu_throttling"]

    intelligence = IncidentIntelligence(
        findings=findings,
        root_causes=[],
        correlations=[],
        timeline=[],
    )
    context = AIContext(incident, intelligence)
    prompt = PromptBuilder().build(context)

    assert "# Diagnoses" in prompt
    assert "CPU contention detected" in prompt
    assert "high_cpu_usage" in prompt
    assert "cpu_throttling" in prompt
