from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from kubesage.api.app import app
from kubesage.api.dependencies import get_incident_service
from kubesage.models.ai_report import AIReport
from kubesage.models.analysis import Analysis
from kubesage.models.incident import Incident

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
            incident=Incident(namespace="default", pod="ai-demo-app", phase="Pending"),
            findings=[],
            report=AIReport(
                summary="Pod is failing",
                root_cause="Redis unavailable",
                evidence=["Check redis connectivity"],
                recommendations=["kubectl logs pod"],
                additional_investigations=["kubectl logs pod"],
            ),
            duration_ms=1000,
        )


def override_service() -> FakeIncidentService:
    return FakeIncidentService()


def test_analyze() -> None:
    with TestClient(app) as client:
        app.dependency_overrides[get_incident_service] = override_service

        response = client.post(
            "/api/v1/analyze",
            json={
                "namespace": "default",
                "pod": "ai-demo-app",
            },
        )

        assert response.status_code == 200
        assert response.json()["root_cause"] == "Redis unavailable"
