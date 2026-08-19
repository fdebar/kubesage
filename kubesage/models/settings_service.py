from enum import StrEnum


class SettingsService(StrEnum):
    PROMETHEUS = "prometheus"
    LOKI = "loki"
    OPENTELEMETRY = "opentelemetry"
    AI = "ai"
