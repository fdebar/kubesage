import os
from dataclasses import dataclass

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
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "ollama")
    openai_url: str = os.getenv("OPENAI_URL", "")

    prometheus_url: str = os.getenv("PROMETHEUS_URL", "")
    prometheus_timeout: int = int(os.getenv("PROMETHEUS_TIMEOUT", "5"))

    otlp_endpoint: str = os.getenv("OTLP_ENDPOINT", "")

    loki_url: str = os.getenv("LOKI_URL", "")
    loki_timeout: int = int(os.getenv("LOKI_TIMEOUT", "5"))
    loki_query_limit: int = int(os.getenv("LOKI_QUERY_LIMIT", "500"))

    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./kubesage.db")


settings = Settings()
