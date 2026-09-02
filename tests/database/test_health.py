from unittest.mock import MagicMock, patch

import pytest

from kubesage.database.health import check_database_availability
from kubesage.utils.exceptions import DatabaseAvailabilityError


class TestCheckDatabaseAvailability:
    def test_database_is_available_and_initialized(self) -> None:
        connection = MagicMock()
        result = MagicMock()
        result.scalar.return_value = "abc123"
        connection.execute.return_value = result

        with patch("kubesage.database.health.engine.connect") as connect:
            connect.return_value.__enter__.return_value = connection
            check_database_availability()

        connection.execute.assert_called_once()

    def test_database_is_not_initialized(self) -> None:
        connection = MagicMock()
        result = MagicMock()
        result.scalar.return_value = None
        connection.execute.return_value = result

        with patch("kubesage.database.health.engine.connect") as connect:
            connect.return_value.__enter__.return_value = connection

            with pytest.raises(
                DatabaseAvailabilityError,
                match="Database is not initialized",
            ):
                check_database_availability()

    def test_database_is_unavailable(self) -> None:
        original_error = Exception("connection refused")

        with (
            patch(
                "kubesage.database.health.engine.connect",
                side_effect=original_error,
            ),
            pytest.raises(
                DatabaseAvailabilityError,
                match="Database is unavailable",
            ) as exc_info,
        ):
            check_database_availability()

        assert exc_info.value.__cause__ is original_error

    def test_database_availability_error_is_not_wrapped_again(self) -> None:
        connection = MagicMock()
        result = MagicMock()
        result.scalar.return_value = None
        connection.execute.return_value = result

        with patch("kubesage.database.health.engine.connect") as connect:
            connect.return_value.__enter__.return_value = connection

            with pytest.raises(
                DatabaseAvailabilityError,
                match="Database is not initialized",
            ) as exc_info:
                check_database_availability()

        assert exc_info.value.__cause__ is None
