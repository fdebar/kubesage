from unittest.mock import MagicMock, patch

from kubesage.models.ai_report import AIReport
from kubesage.models.container import ContainerSnapshot
from kubesage.models.finding import Finding, ResourceRef, Severity
from kubesage.models.incident import Incident
from kubesage.models.log import LogSnapshot
from kubesage.services.incident_service import IncidentService


@patch("kubesage.services.incident_service.IncidentBuilder")
def test_analyze_flow(incident_builder_cls: MagicMock) -> None:
    incident = Incident(
        namespace="default",
        pod="my-pod",
        phase="Running",
        containers=[
            ContainerSnapshot(
                name="nginx",
                image="nginx:1.25.0",
                ready=True,
                restart_count=1,
            )
        ],
        events=[],
        kubernetes_logs=LogSnapshot(
            source="kubernetes",
            lines=[],
        ),
        loki_logs=None,
        prometheus=None,
        metrics=None,
    )

    incident_builder = MagicMock()
    incident_builder.collect.return_value = incident
    incident_builder_cls.return_value = incident_builder

    findings = [
        Finding(
            rule="high_memory_usage",
            severity=Severity.WARNING,
            title="High memory usage",
            description="High memory usage",
            resource=ResourceRef(kind="Pod", name="test", namespace="test"),
        ),
    ]
    engine = MagicMock()
    engine.analyze.return_value = findings

    context = MagicMock()
    context_builder = MagicMock()
    context_builder.build.return_value = context

    prompt = MagicMock()
    prompt_builder = MagicMock()
    prompt_builder.build.return_value = prompt

    report = AIReport(summary="Empty", root_cause="Empty")
    ai = MagicMock()
    ai.analyze.return_value = report

    service = IncidentService(
        analysis_repository=MagicMock(),
        kubernetes=MagicMock(),
        prometheus=MagicMock(),
        metrics=MagicMock(),
        loki=MagicMock(),
        ai=ai,
        engine=engine,
        ai_context_builder=context_builder,
        prompt_builder=prompt_builder,
        container_snapshot_builder=MagicMock(),
    )

    analysis = service.analyze("default", "my-pod")

    assert analysis.report == report
    assert analysis.incident == incident
    assert analysis.findings == findings

    incident_builder.collect.assert_called_once_with("default", "my-pod")
    engine.analyze.assert_called_once_with(incident)
    context_builder.build.assert_called_once_with(incident, findings)
    prompt_builder.build.assert_called_once_with(context)
    ai.analyze.assert_called_once_with(prompt)
