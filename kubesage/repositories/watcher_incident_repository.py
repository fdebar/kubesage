from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from kubesage.database.models.watcher_incident import WatcherIncidentModel

WatcherIncidentStatus = Literal["active", "resolved"]


class WatcherIncidentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def link_analysis(self, incident_id: str, analysis_id: str) -> bool:
        incident = self.session.get(WatcherIncidentModel, incident_id)
        if incident is None:
            return False
        if incident.analysis_id == analysis_id:
            return True
        if incident.analysis_id is not None:
            return False

        incident.analysis_id = analysis_id
        self.session.commit()

        return True

    def list_incidents(
        self,
        limit: int = 20,
        offset: int = 0,
        status: WatcherIncidentStatus | None = None,
        namespace: str | None = None,
    ) -> list[WatcherIncidentModel]:
        statement = select(WatcherIncidentModel)
        if status is not None:
            statement = statement.where(WatcherIncidentModel.status == status)
        if namespace is not None:
            statement = statement.where(WatcherIncidentModel.namespace == namespace)

        statement = (
            statement.order_by(
                WatcherIncidentModel.first_seen_at.desc(),
                WatcherIncidentModel.id,
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.execute(statement).scalars().all())

    def count(
        self,
        status: WatcherIncidentStatus | None = None,
        namespace: str | None = None,
    ) -> int:
        statement = select(func.count(WatcherIncidentModel.id))
        if status is not None:
            statement = statement.where(WatcherIncidentModel.status == status)
        if namespace is not None:
            statement = statement.where(WatcherIncidentModel.namespace == namespace)
        return self.session.scalar(statement) or 0
