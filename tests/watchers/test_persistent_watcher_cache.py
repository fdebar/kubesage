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
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from kubesage.database.base import Base
from kubesage.watchers.deduplication_repository import (
    IncidentDeduplicationRepository,
)
from kubesage.watchers.incident_deduplicator import IncidentDeduplicator
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


def make_pod(waiting_reason: str | None = None) -> V1Pod:
    state = (
        V1ContainerState(waiting=V1ContainerStateWaiting(reason=waiting_reason))
        if waiting_reason
        else V1ContainerState(running=V1ContainerStateRunning())
    )
    return V1Pod(
        metadata=V1ObjectMeta(
            name="api",
            namespace="production",
            uid="pod-uid",
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
