# database/health.py

from sqlalchemy import text

from kubesage.database.session import engine
from kubesage.utils.exceptions import DatabaseAvailabilityError


def check_database_availability() -> None:
    """Check if the database is available, raise DatabaseAvailabilityError if not."""

    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()

            if version is None:
                raise DatabaseAvailabilityError("Database is not initialized")
    except Exception as err:
        raise DatabaseAvailabilityError("Database is not initialized") from err
