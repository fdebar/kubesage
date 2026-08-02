from sqlalchemy.orm import Session

from kubesage.repositories.analysis_repository import AnalysisRepository


def get_analysis_repository(session: Session) -> AnalysisRepository:
    return AnalysisRepository(session)
