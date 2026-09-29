from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from kubernetes.client import (
    V1ContainerState,
    V1ContainerStateRunning,
    V1ContainerStateWaiting,
    V1ContainerStatus,
    V1ObjectMeta,
    V1Pod,
    V1PodStatus,
)
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from kubesage.database.base import Base
from kubesage.database.models.watcher_incident import WatcherIncidentModel
from kubesage.watchers.deduplication_repository import (
    IncidentDeduplicationRepository,
)
from kubesage.watchers.incident_deduplicator import IncidentDeduplicator
from kubesage.watchers.incident_lifecycle_repository import (
    WatcherIncidentLifecycleRepository,
)
from kubesage.watchers.models.incident_trigger import IncidentTrigger
from kubesage.watchers.pod_state_cache import PodStateCache
from kubesage.watchers.pod_state_diff_builder import PodStateDiffBuilder
from kubesage.watchers.state_repository import WatcherPodStateRepository


@pytest.fixture
def session_factory() -> Generator[sessionmaker[Session]]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, expire_on_commit=False)
    engine.dispose()


def make_pod(waiting_reason: str | None = None, uid: str = "pod-uid") -> V1Pod:
    state = (
        V1ContainerState(waiting=V1ContainerStateWaiting(reason=waiting_reason))
        if waiting_reason
        else V1ContainerState(running=V1ContainerStateRunning())
    )
    return V1Pod(
        metadata=V1ObjectMeta(
            name="api",
            namespace="production",
            uid=uid,
            resource_version="42",
        ),
        status=V1PodStatus(
            phase="Running",
            container_statuses=[
                V1ContainerStatus(
                    name="app",
                    image="example/api:latest",
                    image_id="sha256:abc",
                    ready=waiting_reason is None,
                    restart_count=2,
                    state=state,
                )
            ],
        ),
    )


def make_trigger(reason: str = "CrashLoopBackOff") -> IncidentTrigger:
    return IncidentTrigger(
        reason=reason,
        namespace="production",
        pod="api",
        pod_uid="pod-uid",
        resource_version="42",
        occurred_at=datetime.now(UTC),
    )


def test_pod_state_survives_cache_recreation_and_detects_transition(
    session_factory: sessionmaker[Session],
) -> None:
    repository = WatcherPodStateRepository(session_factory)
    cache_before_restart = PodStateCache(repository)
    cache_before_restart.update(make_pod())

    cache_after_restart = PodStateCache(repository)
    previous = cache_after_restart.get("production", "pod-uid")
    current = make_pod(waiting_reason="CrashLoopBackOff")

    assert previous is not None
    diff = PodStateDiffBuilder().build(previous, current)
    assert diff.waiting_reason_changed is True
    assert diff.previous_waiting_reason is None
    assert diff.current_waiting_reason == "CrashLoopBackOff"


def test_pod_state_replace_removes_rows_for_deleted_pods(
    session_factory: sessionmaker[Session],
) -> None:
    repository = WatcherPodStateRepository(session_factory)
    cache = PodStateCache(repository)
    cache.update(make_pod())

    cache.replace([])

    restarted_cache = PodStateCache(repository)
    assert restarted_cache.size() == 0


def test_deduplication_survives_deduplicator_recreation(
    session_factory: sessionmaker[Session],
) -> None:
    repository = IncidentDeduplicationRepository(session_factory)
    first_process = IncidentDeduplicator(repository=repository)
    second_process = IncidentDeduplicator(repository=repository)
    trigger = make_trigger()

    assert first_process.should_process(trigger) is True
    assert second_process.should_process(trigger) is False


def test_deduplication_expiry_and_forget_are_persisted(
    session_factory: sessionmaker[Session],
) -> None:
    repository = IncidentDeduplicationRepository(session_factory)
    trigger = make_trigger()

    assert repository.claim(trigger, timedelta(seconds=-1)) is True
    assert repository.claim(trigger, timedelta(minutes=5)) is True
    repository.forget(trigger)

    assert repository.claim(trigger, timedelta(minutes=5)) is True


def test_deduplication_keeps_different_reasons_independent(
    session_factory: sessionmaker[Session],
) -> None:
    repository = IncidentDeduplicationRepository(session_factory)

    assert repository.claim(make_trigger(), timedelta(minutes=5)) is True
    assert (
        repository.claim(make_trigger("ImagePullBackOff"), timedelta(minutes=5)) is True
    )


def test_watcher_incident_is_resolved_when_pod_recovers(
    session_factory: sessionmaker[Session],
) -> None:
    repository = WatcherIncidentLifecycleRepository(session_factory)

    repository.sync_pod(
        make_pod(waiting_reason="CrashLoopBackOff"),
        current_reason="CrashLoopBackOff",
        current_message="Container is in CrashLoopBackOff",
    )

    with session_factory() as session:
        incident = session.execute(select(WatcherIncidentModel)).scalar_one()
        assert incident.status == "active"
        assert incident.resolved_at is None
        assert incident.message == "Container is in CrashLoopBackOff"

    repository.sync_pod(make_pod(), current_reason=None)

    with session_factory() as session:
        incident = session.execute(select(WatcherIncidentModel)).scalar_one()
        assert incident.status == "resolved"
        assert incident.resolved_at is not None


def test_watcher_incident_recovery_preserves_each_episode(
    session_factory: sessionmaker[Session],
) -> None:
    repository = WatcherIncidentLifecycleRepository(session_factory)
    failing_pod = make_pod(waiting_reason="CrashLoopBackOff")

    repository.sync_pod(failing_pod, current_reason="CrashLoopBackOff")
    repository.sync_pod(make_pod(), current_reason=None)
    repository.sync_pod(failing_pod, current_reason="CrashLoopBackOff")

    with session_factory() as session:
        incidents = (
            session.execute(
                select(WatcherIncidentModel).order_by(
                    WatcherIncidentModel.first_seen_at
                )
            )
            .scalars()
            .all()
        )

    assert len(incidents) == 2
    assert incidents[0].id != incidents[1].id
    assert [incident.status for incident in incidents].count("resolved") == 1
    assert [incident.status for incident in incidents].count("active") == 1


def test_startup_reconciliation_resolves_incidents_for_missing_pods(
    session_factory: sessionmaker[Session],
) -> None:
    repository = WatcherIncidentLifecycleRepository(session_factory)
    repository.sync_pod(
        make_pod(waiting_reason="CrashLoopBackOff", uid="missing"),
        current_reason="CrashLoopBackOff",
    )
    repository.sync_pod(
        make_pod(waiting_reason="ImagePullBackOff", uid="present"),
        current_reason="ImagePullBackOff",
    )

    repository.resolve_missing_pods(
        [make_pod(waiting_reason="ImagePullBackOff", uid="present")]
    )

    with session_factory() as session:
        incidents = session.execute(select(WatcherIncidentModel)).scalars().all()

    states = {incident.pod_uid: incident.status for incident in incidents}
    assert states == {"missing": "resolved", "present": "active"}
