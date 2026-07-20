from dataclasses import dataclass
from dotenv import load_dotenv
import logging
import os


@dataclass(slots=True)
class Settings:

    load_dotenv()

    log_tail_lines: int = int(os.getenv("LOG_TAIL_LINES", "200"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    openai_model: str = os.getenv("OPENAI_MODEL")
    openai_api_key: str = os.getenv("OPENAI_API_KEY")


settings = Settings()


logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

logger = logging.getLogger("kubesage")
