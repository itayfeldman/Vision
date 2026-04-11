import logging

import uvicorn

from vision.api.app import create_app
from vision.api.dependencies import wire_dependencies
from vision.config import Settings
from vision.infrastructure.database.connection import get_engine, init_db

settings = Settings()

logging.basicConfig(level=settings.log_level)

engine = get_engine(settings.db_path)
init_db(engine)

app = create_app()
wire_dependencies(app, engine)


def main() -> None:
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
    )


if __name__ == "__main__":
    main()
