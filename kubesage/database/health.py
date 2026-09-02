from sqlalchemy import text

from kubesage.database.session import engine
from kubesage.utils.exceptions import DatabaseAvailabilityError


def check_database_availability() -> None:
    """Check if the database is available and initialized."""

    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()

            if version is None:
                raise DatabaseAvailabilityError("Database is not initialized")

    except DatabaseAvailabilityError:
        raise

    except Exception as err:
        raise DatabaseAvailabilityError("Database is unavailable") from err
