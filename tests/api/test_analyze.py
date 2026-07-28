# pyrefly: ignore [missing-import]
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from kubesage.api.app import app
from kubesage.api.dependencies import get_incident_service
from kubesage.models.ai_report import AIReport

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides() -> Generator:
    app.dependency_overrides = {}
    yield
    app.dependency_overrides = {}


class FakeIncidentService:
    def analyze(
        self,
        namespace: str,
        pod: str,
        context: str | None = None,
    ) -> AIReport:
        return AIReport(
            summary="Pod is failing",
            root_cause="Redis unavailable",
            evidence=["Check redis connectivity"],
            recommendations=["kubectl logs pod"],
            additional_investigations=["kubectl logs pod"],
        )


def override_service() -> FakeIncidentService:
    return FakeIncidentService()


def test_analyze() -> None:
    app.dependency_overrides[get_incident_service] = override_service
    response = client.post(
        "/api/v1/analyze", json={"namespace": "default", "pod": "ai-demo-app"}
    )

    assert response.status_code == 200

    body = response.json()
    assert body["root_cause"] == "Redis unavailable"
