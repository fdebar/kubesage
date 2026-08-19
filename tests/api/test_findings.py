from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from kubesage.api.app import app
from kubesage.api.dependencies import get_finding_repository
from kubesage.database.base import Base
from kubesage.database.models.analysis import AnalysisModel
from kubesage.database.models.finding import FindingModel
from kubesage.repositories.finding_repository import FindingRepository


@pytest.fixture
def db_session() -> Generator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient]:
    def override_get_finding_repository() -> FindingRepository:
        return FindingRepository(db_session)

    app.dependency_overrides[get_finding_repository] = override_get_finding_repository

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def create_analysis(
    session: Session,
    *,
    created_at: datetime,
    findings_count: int = 1,
) -> AnalysisModel:
    analysis = AnalysisModel(
        id=str(uuid4()),
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


def test_list_findings_returns_paginated_response(
    client: TestClient,
    db_session: Session,
) -> None:
    analysis = create_analysis(
        db_session,
        created_at=datetime.now(UTC),
        findings_count=1,
    )

    create_finding(
        db_session,
        analysis,
        title="Container restarting",
        severity="CRITICAL",
    )

    db_session.commit()

    response = client.get("/api/v1/findings")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["page"] == 1
    assert data["page_size"] == 20

    assert len(data["items"]) == 1

    finding = data["items"][0]

    assert finding["rule"] == "crash_loop"
    assert finding["kind"] == "observation"
    assert finding["severity"] == "CRITICAL"
    assert finding["title"] == "Container restarting"
    assert finding["description"] == "Test finding"

    assert finding["analysis_id"] == analysis.id


def test_list_findings_returns_resource(
    client: TestClient,
    db_session: Session,
) -> None:
    analysis = create_analysis(db_session, created_at=datetime.now(UTC))
    create_finding(db_session, analysis, title="Container restarting")

    db_session.commit()

    response = client.get("/api/v1/findings")

    assert response.status_code == 200

    finding = response.json()["items"][0]

    assert finding["resource"] == {
        "api_version": "v1",
        "kind": "Pod",
        "namespace": "production",
        "name": "api",
    }


def test_list_findings_returns_null_resource_when_absent(
    client: TestClient,
    db_session: Session,
) -> None:
    analysis = create_analysis(db_session, created_at=datetime.now(UTC))

    create_finding(
        db_session,
        analysis,
        title="Generic issue",
        resource=False,
    )

    db_session.commit()

    response = client.get("/api/v1/findings")
    assert response.status_code == 200

    finding = response.json()["items"][0]
    assert finding["resource"] is None


def test_list_findings_respects_pagination(
    client: TestClient,
    db_session: Session,
) -> None:
    now = datetime.now(UTC)

    for index in range(3):
        analysis = create_analysis(
            db_session,
            created_at=now - timedelta(minutes=index),
        )

        create_finding(db_session, analysis, title=f"Finding {index}")

    db_session.commit()

    response = client.get("/api/v1/findings", params={"page": 2, "page_size": 1})

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert data["page"] == 2
    assert data["page_size"] == 1

    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Finding 1"


def test_list_findings_orders_by_analysis_date(
    client: TestClient,
    db_session: Session,
) -> None:
    now = datetime.now(UTC)

    older = create_analysis(db_session, created_at=now - timedelta(hours=1))
    newer = create_analysis(db_session, created_at=now)

    create_finding(db_session, older, title="Older finding")
    create_finding(db_session, newer, title="Newer finding")

    db_session.commit()

    response = client.get("/api/v1/findings")
    assert response.status_code == 200

    items = response.json()["items"]
    assert len(items) == 2
    assert items[0]["title"] == "Newer finding"
    assert items[1]["title"] == "Older finding"


def test_list_findings_rejects_invalid_page(client: TestClient) -> None:
    response = client.get("/api/v1/findings", params={"page": 0})

    assert response.status_code == 422


def test_list_findings_rejects_invalid_page_size(client: TestClient) -> None:
    response = client.get("/api/v1/findings", params={"page_size": 101})

    assert response.status_code == 422
