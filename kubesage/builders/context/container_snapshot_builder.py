import structlog

from kubesage.models.container import (
    ContainerResources,
    ContainerSnapshot,
    ContainerStatus,
    ContainerUsage,
    PodResources,
)

logger = structlog.get_logger()


class ContainerSnapshotBuilder:
    def build(
        self,
        statuses: list[ContainerStatus],
        usages: list[ContainerUsage] | None,
        resources: PodResources,
    ) -> list[ContainerSnapshot]:
        snapshots = []

        container_resources: dict[str, ContainerResources] = {
            c.name: c for c in resources.containers
        }

        container_usages: dict[str, ContainerUsage] | None = {
            usage.name: usage for usage in (usages or [])
        }

        for status in statuses:
            snapshots.append(
                ContainerSnapshot(
                    name=status.name,
                    image=status.image,
                    ready=status.ready,
                    restart_count=status.restart_count,
                    waiting_reason=status.waiting_reason,
                    waiting_message=status.waiting_message,
                    last_exit_code=status.last_exit_code,
                    last_exit_reason=status.last_exit_reason,
                    resources=container_resources.get(status.name),
                    usage=(
                        container_usages.get(status.name)
                        if container_usages is not None
                        else None
                    ),
                )
            )

        logger.debug(
            "container_snapshot_builder_build_result",
            snapshots=snapshots,
        )

        return snapshots
