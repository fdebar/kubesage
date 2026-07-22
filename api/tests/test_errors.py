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


class FakeErrorService:
    def analyze(
        self,
        namespace,
        pod,
        context=None,
    ):
        raise PodNotFoundError(f"{pod} not found")


def override_service():
    return FakeErrorService()


def test_pod_not_found():
    app.dependency_overrides[get_incident_service] = override_service
    response = client.post(
        "/api/v1/analyze", json={"namespace": "default", "pod": "unknown-pod"}
    )

    assert response.status_code == 404
    body = response.json()

    assert body["error"] == "Pod not found"
