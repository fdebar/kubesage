from dataclasses import dataclass
import os

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    load_dotenv()

    app_name: str = "KubeSage"
    app_version: str = "0.11.0"
    environment: str = os.getenv("ENVIRONMENT", "production")
    log_level: str = os.getenv("LOG_LEVEL", "WARNING")
    log_tail_lines: int = int(os.getenv("LOG_TAIL_LINES", "200"))
    openai_model: str = os.getenv("OPENAI_MODEL", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_url: str = os.getenv("OPENAI_URL", "")
    prometheus_url: str = os.getenv("PROMETHEUS_URL", "")
    prometheus_timeout: int = int(os.getenv("PROMETHEUS_TIMEOUT", "5"))
    otlp_endpoint: str = os.getenv("OTLP_ENDPOINT", "")


settings = Settings()
