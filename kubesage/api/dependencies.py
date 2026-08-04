from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from kubesage.bootstrap import create_analysis_service
from kubesage.database.session import SessionLocal
from kubesage.repositories.analysis_repository import AnalysisRepository
from kubesage.services.analysis_service import AnalysisService
from kubesage.services.dashboard_service import DashboardService
from kubesage.services.kubernetes_service import KubernetesService


def get_db() -> Generator[Session]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def get_analysis_repository(session: Session = Depends(get_db)) -> AnalysisRepository:
    return AnalysisRepository(session)


def get_analysis_service(db: Session = Depends(get_db)) -> AnalysisService:
    return create_analysis_service(db)


def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    return DashboardService(AnalysisRepository(db), KubernetesService())
