from fastapi.testclient import TestClient
from kubesage.api.app import app

client = TestClient(app)


def test_metrics() -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "python_info" in response.text
