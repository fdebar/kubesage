from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)


def test_metrics():
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "python_info" in response.text
