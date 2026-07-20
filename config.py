from dataclasses import dataclass
import os


@dataclass(slots=True)
class Settings:
    log_tail_lines: int = int(os.getenv("LOG_TAIL_LINES", "200"))


settings = Settings()