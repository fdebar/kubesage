from collections.abc import Generator
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from kubesage.database.base import Base
from kubesage.database.models.analysis import AnalysisModel
from kubesage.database.models.watcher_incident import WatcherIncidentModel
from kubesage.watchers.models.incident_trigger import IncidentTrigger
from kubesage.worker import analysis_worker as analysis_worker_module
from kubesage.worker.analysis_worker import AnalysisWorker


@pytest.fixture
def session_factory() -> Generator[sessionmaker[Session]]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    yield factory
    engine.dispose()


def test_worker_links_successful_analysis_to_watcher_episode(
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    incident_id = str(uuid4())
    analysis_id = str(uuid4())
    with session_factory() as session:
        session.add(
            AnalysisModel(
                id=analysis_id,
                namespace="production",
                pod="api",
                pod_uid="pod-uid",
                trigger="watcher",
                phase="CrashLoopBackOff",
                duration_ms=100,
                findings_count=0,
            )
        )
        session.add(
            WatcherIncidentModel(
                id=incident_id,
                namespace="production",
                pod_uid="pod-uid",
                reason="CrashLoopBackOff",
                pod="api",
                status="active",
                first_seen_at=datetime.now(UTC),
                last_seen_at=datetime.now(UTC),
            )
        )
        session.commit()

    analysis_service = MagicMock()
    analysis_service.analyze.return_value = SimpleNamespace(id=analysis_id)
    monkeypatch.setattr(analysis_worker_module, "SessionLocal", session_factory)
    monkeypatch.setattr(
        analysis_worker_module,
        "create_analysis_service",
        lambda _db: analysis_service,
    )

    trigger = IncidentTrigger(
        reason="CrashLoopBackOff",
        namespace="production",
        pod="api",
        pod_uid="pod-uid",
        resource_version="42",
        occurred_at=datetime.now(UTC),
        watcher_incident_id=incident_id,
    )
    worker = AnalysisWorker(deduplicator=MagicMock(), max_retries=1)

    assert worker._process(trigger) is True

    with session_factory() as session:
        incident = session.get(WatcherIncidentModel, incident_id)

    assert incident is not None
    assert incident.analysis_id == analysis_id
    analysis_service.analyze.assert_called_once()
