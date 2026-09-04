import os
from dataclasses import dataclass
from urllib.parse import quote_plus

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    load_dotenv()

    # Application configuration
    app_name: str = "KubeSage"
    app_version: str = "1.0.0-beta"

    # Database configuration
    database_host: str = os.getenv("DATABASE_HOST", "")
    database_port: int = int(os.getenv("DATABASE_PORT", "5432"))
    database_name: str = os.getenv("DATABASE_NAME", "")
    database_user: str = os.getenv("DATABASE_USER", "")
    database_password: str = os.getenv("DATABASE_PASSWORD", "")

    # Environment configuration
    environment: str = os.getenv("ENVIRONMENT", "production")

    # Logging configuration
    log_level: str = os.getenv("LOG_LEVEL", "WARNING")
    log_tail_lines: int = int(os.getenv("LOG_TAIL_LINES", "200"))

    # AI configuration
    ai_provider: str = os.getenv("AI_PROVIDER", "")
    ai_model: str = os.getenv("AI_MODEL", "")
    ai_api_key: str = os.getenv("AI_API_KEY", "")
    ai_url: str = os.getenv("AI_URL", "")

    # Prometheus configuration
    prometheus_url: str = os.getenv("PROMETHEUS_URL", "")
    prometheus_timeout: int = int(os.getenv("PROMETHEUS_TIMEOUT", "5"))

    # OTLP configuration
    otlp_endpoint: str | None = os.getenv("OTLP_ENDPOINT") or None

    # Loki configuration
    loki_url: str = os.getenv("LOKI_URL", "")
    loki_timeout: int = int(os.getenv("LOKI_TIMEOUT", "5"))
    loki_query_limit: int = int(os.getenv("LOKI_QUERY_LIMIT", "500"))
    loki_tenant: str = os.getenv("LOKI_TENANT", "kubesage")

    # Metrics configuration
    metrics_port: int = int(os.getenv("WORKER_EXPOSED_METRICS_PORT", "9090"))

    # AI Timeline configuration
    ai_timeline_max_events: int = int(os.getenv("AI_TIMELINE_MAX_EVENTS", "50"))
    ai_timeline_window_before_seconds: int = int(
        os.getenv("AI_TIMELINE_WINDOW_BEFORE_SECONDS", "30")
    )
    ai_timeline_window_after_seconds: int = int(
        os.getenv("AI_TIMELINE_WINDOW_AFTER_SECONDS", "10")
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://"
            f"{quote_plus(self.database_user)}:"
            f"{quote_plus(self.database_password)}@"
            f"{self.database_host}:"
            f"{self.database_port}/"
            f"{self.database_name}"
        )


settings = Settings()
