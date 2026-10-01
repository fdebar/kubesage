from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from kubesage.api.app import app
from kubesage.api.dependencies import get_watcher_incident_repository
from kubesage.database.base import Base
from kubesage.database.models.analysis import AnalysisModel
from kubesage.database.models.watcher_incident import WatcherIncidentModel
from kubesage.repositories.watcher_incident_repository import (
    WatcherIncidentRepository,
)


@pytest.fixture
def db_session() -> Generator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient]:
    def override_repository() -> WatcherIncidentRepository:
        return WatcherIncidentRepository(db_session)

    app.dependency_overrides[get_watcher_incident_repository] = override_repository
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def add_incident(
    session: Session,
    *,
    namespace: str,
    pod: str,
    status: str,
    first_seen_at: datetime,
) -> WatcherIncidentModel:
    incident = WatcherIncidentModel(
        id=str(uuid4()),
        namespace=namespace,
        pod_uid=f"uid-{pod}",
        reason="CrashLoopBackOff",
        pod=pod,
        status=status,
        first_seen_at=first_seen_at,
        last_seen_at=first_seen_at + timedelta(minutes=1),
        resolved_at=(
            first_seen_at + timedelta(minutes=1) if status == "resolved" else None
        ),
        last_resource_version="42",
        message="Container is restarting",
    )
    session.add(incident)
    return incident


def test_list_watcher_incidents_returns_paginated_lifecycle_data(
    client: TestClient,
    db_session: Session,
) -> None:
    now = datetime.now(UTC)
    add_incident(
        db_session,
        namespace="production",
        pod="newer-api",
        status="active",
        first_seen_at=now,
    )
    add_incident(
        db_session,
        namespace="production",
        pod="older-api",
        status="resolved",
        first_seen_at=now - timedelta(hours=1),
    )
    db_session.commit()

    response = client.get(
        "/api/v1/watcher/incidents",
        params={"page": 2, "page_size": 1},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["page"] == 2
    assert len(data["items"]) == 1
    assert data["items"][0]["pod"] == "older-api"
    assert data["items"][0]["status"] == "resolved"
    assert data["items"][0]["resolved_at"] is not None


def test_list_watcher_incidents_filters_status_and_namespace(
    client: TestClient,
    db_session: Session,
) -> None:
    now = datetime.now(UTC)
    add_incident(
        db_session,
        namespace="production",
        pod="api",
        status="active",
        first_seen_at=now,
    )
    add_incident(
        db_session,
        namespace="staging",
        pod="worker",
        status="resolved",
        first_seen_at=now - timedelta(minutes=1),
    )
    db_session.commit()

    response = client.get(
        "/api/v1/watcher/incidents",
        params={"status": "active", "namespace": "production"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["namespace"] == "production"
    assert data["items"][0]["status"] == "active"


def test_list_watcher_incidents_rejects_unknown_status(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/watcher/incidents",
        params={"status": "open"},
    )

    assert response.status_code == 422


def test_list_watcher_incidents_returns_linked_analyses(
    client: TestClient,
    db_session: Session,
) -> None:
    incident = add_incident(
        db_session,
        namespace="production",
        pod="api",
        status="active",
        first_seen_at=datetime.now(UTC),
    )
    analysis_id = "analysis-1"
    db_session.add(
        AnalysisModel(
            id=analysis_id,
            namespace="production",
            pod="api",
            pod_uid=incident.pod_uid,
            trigger="watcher",
            phase="CrashLoopBackOff",
            duration_ms=100,
            findings_count=0,
        )
    )
    incident.analysis_id = analysis_id
    db_session.commit()

    response = client.get("/api/v1/watcher/incidents")

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["analysis_id"] == analysis_id
