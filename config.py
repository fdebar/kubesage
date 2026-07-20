from dataclasses import dataclass
import logging
import os


@dataclass(slots=True)
class Settings:

    log_tail_lines: int = int(
        os.getenv("LOG_TAIL_LINES", "200")
    )

    log_level: str = os.getenv(
        "LOG_LEVEL",
        "INFO"
    )


settings = Settings()


logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

logger = logging.getLogger("kubesage")
