"""Application configuration via environment variables."""

import os


class Settings:
    host: str = os.getenv("VISION_HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8080"))
    db_path: str = os.getenv("VISION_DB_PATH", "vision.db")
    log_level: str = os.getenv("VISION_LOG_LEVEL", "INFO")
