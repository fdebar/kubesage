from datetime import UTC, datetime
from uuid import uuid4

from kubesage.database.models.analysis import AnalysisModel
from kubesage.database.models.incident_snapshot import IncidentSnapshotModel
from kubesage.mappers.analysis_mapper import AnalysisMapper
from kubesage.models.analysis import Analysis, AnalysisTrigger
from kubesage.models.incident import Incident
from kubesage.models.incident_intelligence import IncidentIntelligence


def make_incident_data(*, observed_at: datetime | None = None) -> dict:
    data = {
        "namespace": "default",
        "pod": "kubesage-crashloop",
        "pod_uid": "5ba84d4a-06cd-4998-8a6e-f123456789ab",
        "phase": "Running",
        "containers": [],
    }

    if observed_at is not None:
        data["observed_at"] = observed_at.isoformat()

    return data


def make_analysis_model(
    *,
    incident_data: dict,
    created_at: datetime | None = None,
) -> AnalysisModel:
    created_at = created_at or datetime.now(UTC)

    model = AnalysisModel(
        id=str(uuid4()),
        namespace="default",
        pod="kubesage-crashloop",
        pod_uid="5ba84d4a-06cd-4998-8a6e-f123456789ab",
        duration_ms=100,
        summary=None,
        highest_severity=None,
        phase="Running",
        findings_count=0,
        created_at=created_at,
        trigger=AnalysisTrigger.CLI,
    )

    model.incident_snapshot = IncidentSnapshotModel(
        analysis_id=model.id,
        data=incident_data,
    )

    model.findings = []
    model.correlations = []
    model.root_causes = []
    model.report = None

    return model


def test_to_domain_restores_observed_at_from_snapshot() -> None:
    observed_at = datetime(2026, 8, 31, 8, 0, 16, tzinfo=UTC)

    model = make_analysis_model(
        incident_data=make_incident_data(observed_at=observed_at),
    )

    analysis = AnalysisMapper.to_domain(model)

    assert analysis.incident.observed_at == observed_at


def test_to_domain_falls_back_to_created_at_when_observed_at_is_missing() -> None:
    created_at = datetime(2026, 8, 31, 8, 30, 0, tzinfo=UTC)

    model = make_analysis_model(
        incident_data=make_incident_data(),
        created_at=created_at,
    )
    analysis = AnalysisMapper.to_domain(model)

    assert analysis.incident.observed_at == created_at


def test_to_domain_does_not_override_existing_observed_at() -> None:
    observed_at = datetime(2026, 8, 31, 8, 0, 16, tzinfo=UTC)
    created_at = datetime(2026, 8, 31, 9, 0, 0, tzinfo=UTC)

    model = make_analysis_model(
        incident_data=make_incident_data(observed_at=observed_at),
        created_at=created_at,
    )
    analysis = AnalysisMapper.to_domain(model)

    assert analysis.incident.observed_at == observed_at
    assert analysis.incident.observed_at != created_at


def test_to_model_persists_observed_at() -> None:
    observed_at = datetime(2026, 8, 31, 8, 0, 16)

    incident = Incident(
        namespace="default",
        pod="kubesage-crashloop",
        pod_uid="5ba84d4a-06cd-4998-8a6e-f123456789ab",
        phase="Running",
        containers=[],
        observed_at=observed_at,
    )

    analysis = Analysis(
        id=uuid4(),
        incident=incident,
        report=None,
        duration_ms=100,
        intelligence=IncidentIntelligence(
            findings=[],
            timeline=[],
            correlations=[],
            root_causes=[],
            recommendations=[],
        ),
        created_at=datetime(2026, 8, 31, 9, 0, 0),
        trigger=AnalysisTrigger.CLI,
    )

    model = AnalysisMapper.to_model(analysis)

    assert model.incident_snapshot is not None
    assert model.incident_snapshot.data["observed_at"] == observed_at.isoformat()


def test_to_model_then_to_domain_preserves_observed_at() -> None:
    observed_at = datetime(2026, 8, 31, 8, 0, 16, tzinfo=UTC)

    incident = Incident(
        namespace="default",
        pod="kubesage-crashloop",
        pod_uid="5ba84d4a-06cd-4998-8a6e-f123456789ab",
        phase="Running",
        containers=[],
        observed_at=observed_at,
    )

    analysis = Analysis(
        id=uuid4(),
        incident=incident,
        report=None,
        duration_ms=100,
        intelligence=IncidentIntelligence(
            findings=[],
            timeline=[],
            correlations=[],
            root_causes=[],
            recommendations=[],
        ),
        created_at=datetime(2026, 8, 31, 9, 0, 0, tzinfo=UTC),
        trigger=AnalysisTrigger.CLI,
    )

    model = AnalysisMapper.to_model(analysis)
    restored = AnalysisMapper.to_domain(model)

    assert restored.incident.observed_at == observed_at
