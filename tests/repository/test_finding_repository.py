import uuid
from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from kubesage.database.base import Base
from kubesage.database.models.analysis import AnalysisModel
from kubesage.database.models.finding import FindingModel
from kubesage.repositories.finding_repository import FindingRepository


@pytest.fixture
def db_session() -> Generator[Session]:
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def create_analysis(
    session: Session,
    *,
    created_at: datetime,
    findings_count: int = 1,
) -> AnalysisModel:
    analysis = AnalysisModel(
        id=str(uuid.uuid4()),
        namespace="production",
        pod="api",
        trigger="api",
        phase="CrashLoopBackOff",
        highest_severity="HIGH",
        summary="Test analysis",
        duration_ms=100,
        created_at=created_at,
        findings_count=findings_count,
    )

    session.add(analysis)
    session.flush()

    return analysis


def create_finding(
    session: Session,
    analysis: AnalysisModel,
    *,
    title: str,
    severity: str = "HIGH",
    resource: bool = True,
) -> FindingModel:
    finding = FindingModel(
        analysis_id=analysis.id,
        rule="crash_loop",
        kind="observation",
        severity=severity,
        title=title,
        description="Test finding",
        resource_api_version="v1" if resource else None,
        resource_kind="Pod" if resource else None,
        resource_namespace="production" if resource else None,
        resource_name="api" if resource else None,
    )

    session.add(finding)
    session.flush()

    return finding


def test_list_findings_returns_findings(db_session: Session) -> None:
    now = datetime.now(UTC)

    analysis = create_analysis(db_session, created_at=now)
    create_finding(db_session, analysis, title="Container restarting")

    repository = FindingRepository(db_session)
    findings = repository.list_findings()

    assert len(findings) == 1

    finding = findings[0]

    assert finding.title == "Container restarting"
    assert finding.severity.value == "HIGH"
    assert finding.analysis_id == uuid.UUID(analysis.id)


def test_list_findings_restores_resource(db_session: Session) -> None:
    analysis = create_analysis(db_session, created_at=datetime.now(UTC))
    create_finding(db_session, analysis, title="Container restarting")

    repository = FindingRepository(db_session)
    finding = repository.list_findings()[0]

    assert finding.resource is not None
    assert finding.resource.api_version == "v1"
    assert finding.resource.kind == "Pod"
    assert finding.resource.namespace == "production"
    assert finding.resource.name == "api"


def test_list_findings_without_resource(db_session: Session) -> None:
    analysis = create_analysis(db_session, created_at=datetime.now(UTC))

    create_finding(db_session, analysis, title="Generic issue", resource=False)

    repository = FindingRepository(db_session)
    finding = repository.list_findings()[0]

    assert finding.resource is None


def test_list_findings_orders_by_analysis_date(
    db_session: Session,
) -> None:
    now = datetime.now(UTC)

    older = create_analysis(db_session, created_at=now - timedelta(hours=2))
    newer = create_analysis(db_session, created_at=now)

    create_finding(db_session, older, title="Older finding")
    create_finding(db_session, newer, title="Newer finding")

    repository = FindingRepository(db_session)
    findings = repository.list_findings()

    assert [finding.title for finding in findings] == ["Newer finding", "Older finding"]


def test_list_findings_respects_limit(db_session: Session) -> None:
    now = datetime.now(UTC)

    for index in range(3):
        analysis = create_analysis(
            db_session,
            created_at=now - timedelta(minutes=index),
        )
        create_finding(db_session, analysis, title=f"Finding {index}")

    repository = FindingRepository(db_session)
    findings = repository.list_findings(limit=2)

    assert len(findings) == 2


def test_list_findings_respects_offset(db_session: Session) -> None:
    now = datetime.now(UTC)

    for index in range(3):
        analysis = create_analysis(
            db_session,
            created_at=now - timedelta(minutes=index),
        )
        create_finding(db_session, analysis, title=f"Finding {index}")

    repository = FindingRepository(db_session)
    findings = repository.list_findings(limit=10, offset=1)

    assert len(findings) == 2
    assert findings[0].title == "Finding 1"


def test_count_returns_total_findings(db_session: Session) -> None:
    analysis = create_analysis(db_session, created_at=datetime.now(UTC))
    create_finding(db_session, analysis, title="Finding 1")
    create_finding(db_session, analysis, title="Finding 2")

    repository = FindingRepository(db_session)

    assert repository.count() == 2
