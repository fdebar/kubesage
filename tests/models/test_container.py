from datetime import UTC, datetime

from kubesage.models.container import ContainerStatus


def test_container_status_supports_lifecycle_timestamps() -> None:
    started_at = datetime(2026, 8, 30, 12, 30, 0, tzinfo=UTC)
    finished_at = datetime(2026, 8, 30, 12, 32, 41, tzinfo=UTC)

    container = ContainerStatus(
        name="api",
        image="api:1.0",
        ready=False,
        restart_count=1,
        last_exit_code=137,
        last_exit_reason="OOMKilled",
        started_at=started_at,
        finished_at=finished_at,
    )

    assert container.started_at == started_at
    assert container.finished_at == finished_at


def test_container_status_lifecycle_timestamps_are_optional() -> None:
    container = ContainerStatus(
        name="api",
        image="api:1.0",
        ready=True,
        restart_count=0,
    )

    assert container.started_at is None
    assert container.finished_at is None
