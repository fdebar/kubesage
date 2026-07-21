from dataclasses import dataclass
from dotenv import load_dotenv
import logging
import os


@dataclass(slots=True)
class Settings:
    load_dotenv()

    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_tail_lines: int = int(os.getenv("LOG_TAIL_LINES", "200"))
    openai_model: str = os.getenv("OPENAI_MODEL")
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    prometheus_url: str = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
    prometheus_timeout: int = int(os.getenv("PROMETHEUS_TIMEOUT", "5"))


settings = Settings()


logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

logger = logging.getLogger("kubesage")
