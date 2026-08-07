from unittest.mock import MagicMock, patch

from kubesage.api.routers.system import health


def test_health_returns_healthy_when_ai_is_available() -> None:
    provider = MagicMock()
    provider.is_server_reachable.return_value = True

    with patch("kubesage.api.routers.system.create_ai_provider", return_value=provider):
        response = health()

    assert response == {
        "status": "healthy",
        "components": {
            "ai": "up",
            "kubernetes": "up",
            "prometheus": "up",
        },
        "version": "0.8.0",
    }

    provider.is_server_reachable.assert_called_once()


def test_health_returns_ai_down_when_provider_is_unreachable() -> None:
    provider = MagicMock()
    provider.is_server_reachable.return_value = False

    with patch("kubesage.api.routers.system.create_ai_provider", return_value=provider):
        response = health()

    assert response["status"] == "healthy"
    assert response["components"] == {
        "ai": "down",
        "kubernetes": "up",
        "prometheus": "up",
    }

    provider.is_server_reachable.assert_called_once()


def test_health_creates_ai_provider() -> None:
    provider = MagicMock()
    provider.is_server_reachable.return_value = True

    with patch(
        "kubesage.api.routers.system.create_ai_provider", return_value=provider
    ) as create_provider:
        health()

    create_provider.assert_called_once()
