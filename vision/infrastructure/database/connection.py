"""SQLite database connection management."""

from sqlalchemy import MetaData, create_engine
from sqlalchemy.engine import Engine

metadata = MetaData()


def get_engine(db_path: str = "vision.db") -> Engine:
    return create_engine(f"sqlite:///{db_path}")


def init_db(engine: Engine) -> None:
    import vision.infrastructure.database.models as _models  # noqa: F401

    metadata.create_all(engine)
