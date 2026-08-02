# pyrefly: ignore [missing-import]
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from kubesage.api.app import app
from kubesage.api.dependencies import get_analysis_service
from kubesage.utils.exceptions import PodNotFoundError

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides() -> Generator:
    app.dependency_overrides = {}
    yield
    app.dependency_overrides = {}


class FakeErrorService:
    def analyze(
        self,
        namespace: str,
        pod: str,
        context: str | None = None,
    ) -> None:
        raise PodNotFoundError(f"{pod} not found")


def override_service() -> FakeErrorService:
    return FakeErrorService()


def test_pod_not_found() -> None:
    app.dependency_overrides[get_analysis_service] = override_service
    response = client.post(
        "/api/v1/analyze", json={"namespace": "default", "pod": "unknown-pod"}
    )

    assert response.status_code == 404
    body = response.json()

    assert body["error"] == "Pod not found"
