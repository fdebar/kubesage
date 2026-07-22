import pytest
from fastapi.testclient import TestClient
from api.app import app
from api.dependencies import get_incident_service
from utils.exceptions import PodNotFoundError


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides():
    app.dependency_overrides = {}
    yield
    app.dependency_overrides = {}


class FakeIncidentService:
    def analyze(
        self,
        namespace,
        pod,
        context=None,
    ):
        return {
            "summary": "Pod is failing",
            "severity": "critical",
            "root_cause": "Redis unavailable",
            "recommendations": ["Check redis connectivity"],
            "kubectl_commands": ["kubectl logs pod"],
        }


def override_service():
    return FakeIncidentService()


def test_analyze():
    app.dependency_overrides[get_incident_service] = override_service
    response = client.post(
        "/api/v1/analyze", json={"namespace": "default", "pod": "ai-demo-app"}
    )

    assert response.status_code == 200

    body = response.json()
    assert body["severity"] == "critical"
