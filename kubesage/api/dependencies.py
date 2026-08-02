from fastapi import Depends
from sqlalchemy.orm import Session

from kubesage.bootstrap import create_incident_service
from kubesage.database.dependencies import get_db
from kubesage.repositories.analysis_repository import AnalysisRepository
from kubesage.services.analysis_service import AnalysisService


def get_analysis_service(db: Session = Depends(get_db)) -> AnalysisService:
    repository = AnalysisRepository(db)

    return AnalysisService(
        incident_service=create_incident_service(db),
        repository=repository,
    )
