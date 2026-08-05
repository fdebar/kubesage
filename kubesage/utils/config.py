import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    load_dotenv()

    # Application configuration
    app_name: str = "KubeSage"
    app_version: str = "0.11.0"

    # Database configuration
    database_url: str = os.environ["DATABASE_URL"]

    # Environment configuration
    environment: str = os.getenv("ENVIRONMENT", "production")

    # Logging configuration
    log_level: str = os.getenv("LOG_LEVEL", "WARNING")
    log_tail_lines: int = int(os.getenv("LOG_TAIL_LINES", "200"))

    # OpenAI configuration
    openai_model: str = os.getenv("OPENAI_MODEL", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "ollama")
    openai_url: str = os.getenv("OPENAI_URL", "")

    # Prometheus configuration
    prometheus_url: str = os.getenv("PROMETHEUS_URL", "")
    prometheus_timeout: int = int(os.getenv("PROMETHEUS_TIMEOUT", "5"))

    # OTLP configuration
    otlp_endpoint: str = os.getenv("OTLP_ENDPOINT", "")

    # Loki configuration
    loki_url: str = os.getenv("LOKI_URL", "")
    loki_timeout: int = int(os.getenv("LOKI_TIMEOUT", "5"))
    loki_query_limit: int = int(os.getenv("LOKI_QUERY_LIMIT", "500"))

    # Metrics configuration
    metrics_port: int = int(os.getenv("WORKER_EXPOSED_METRICS_PORT", "9090"))


settings = Settings()
