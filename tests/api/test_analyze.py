# pyrefly: ignore [missing-import]
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from kubesage.api.app import app
from kubesage.api.dependencies import get_incident_service


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
    ) -> dict:
        return {
            "summary": "Pod is failing",
            "severity": "critical",
            "root_cause": "Redis unavailable",
            "recommendations": ["Check redis connectivity"],
            "kubectl_commands": ["kubectl logs pod"],
        }


def override_service() -> FakeIncidentService:
    return FakeIncidentService()


def test_analyze() -> None:
    app.dependency_overrides[get_incident_service] = override_service
    response = client.post(
        "/api/v1/analyze", json={"namespace": "default", "pod": "ai-demo-app"}
    )

    assert response.status_code == 200

    body = response.json()
    assert body["severity"] == "critical"
