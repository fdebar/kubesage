from services.incident_service import IncidentService

incident_service = IncidentService()


def get_incident_service():
    return incident_service
