from fastapi import Depends
from sqlalchemy.orm import Session

from kubesage.bootstrap import create_incident_service
from kubesage.database.dependencies import get_db
from kubesage.services.incident_service import IncidentService


def get_incident_service(db: Session = Depends(get_db)) -> IncidentService:
    return create_incident_service(db)
