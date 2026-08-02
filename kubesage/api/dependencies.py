from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from kubesage.bootstrap import create_incident_service
from kubesage.database.session import SessionLocal
from kubesage.repositories.analysis_repository import AnalysisRepository
from kubesage.services.analysis_service import AnalysisService


def get_db() -> Generator[Session]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def get_analysis_repository(session: Session = Depends(get_db)) -> AnalysisRepository:
    return AnalysisRepository(session)


def get_analysis_service(db: Session = Depends(get_db)) -> AnalysisService:
    repository = AnalysisRepository(db)

    return AnalysisService(
        incident_service=create_incident_service(db),
        repository=repository,
    )
