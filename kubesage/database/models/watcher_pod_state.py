from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from kubesage.database.base import Base


class WatcherPodStateModel(Base):
    __tablename__ = "watcher_pod_states"

    namespace: Mapped[str] = mapped_column(String(255), primary_key=True)
    pod_uid: Mapped[str] = mapped_column(String(255), primary_key=True)
    state: Mapped[dict] = mapped_column(JSON, nullable=False)
