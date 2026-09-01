from collections.abc import Generator
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from kubesage.api.app import app
from kubesage.api.dependencies import get_analysis_service
from kubesage.models.ai_report import AIReport, EvidenceReference
from kubesage.models.analysis import Analysis, AnalysisTrigger
from kubesage.models.incident import Incident
from kubesage.models.incident_intelligence import IncidentIntelligence

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides() -> Generator:
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


class FakeIncidentService:
    def analyze(
        self,
        namespace: str,
        pod: str,
        context: str | None = None,
    ) -> Analysis:
        return Analysis(
            incident=Incident(
                namespace=namespace,
                pod=pod,
                phase="Pending",
                observed_at=datetime.now(),
            ),
            findings=[],
            report=AIReport(
                summary="Pod is failing",
                root_cause="Redis unavailable",
                evidence=[
                    EvidenceReference(
                        id="123",
                        description="Check redis connectivity",
                    )
                ],
                recommendations=["kubectl logs pod"],
                additional_investigations=["kubectl logs pod"],
            ),
            duration_ms=1000,
            intelligence=IncidentIntelligence(),
            trigger=AnalysisTrigger.API,
        )


def override_service() -> FakeIncidentService:
    return FakeIncidentService()


def test_analyze() -> None:
    with TestClient(app) as client:
        app.dependency_overrides[get_analysis_service] = override_service

        response = client.post(
            "/api/v1/analyze",
            json={
                "namespace": "default",
                "pod": "ai-demo-app",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"]
    assert data["trigger"] == "api"

    assert data["incident"] == {
        "namespace": "default",
        "pod": "ai-demo-app",
        "pod_uid": None,
        "phase": "Pending",
    }

    assert data["highest_severity"] is None
    assert data["findings_count"] == 0
    assert data["findings"] == []
    assert data["correlations"] == []
    assert data["root_causes"] == []

    assert data["report"]["summary"] == "Pod is failing"
    assert data["report"]["root_cause"] == "Redis unavailable"
    assert data["report"]["evidence"] == [
        {
            "id": "123",
            "description": "Check redis connectivity",
            "source": None,
        }
    ]
    assert data["report"]["recommendations"] == ["kubectl logs pod"]
    assert data["report"]["additional_investigations"] == ["kubectl logs pod"]

    assert data["duration_ms"] == 1000
    assert data["created_at"]
