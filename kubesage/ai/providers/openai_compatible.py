import time

import structlog
from openai import APIConnectionError, APIStatusError, Client
from opentelemetry import trace

from kubesage.models.ai_report import AIReport
from kubesage.observability.metrics import (
    LLM_DURATION,
    LLM_REQUESTS,
    LLM_TOKENS,
)

logger = structlog.get_logger()
tracer = trace.get_tracer(__name__)


class OpenAICompatibleProvider:
    def __init__(self, client: Client, model: str) -> None:
        self._client = client
        self._model = model

    def analyze(self, prompt: str) -> AIReport:
        logger.info("llm_start", model=self._model)

        with tracer.start_as_current_span("llm.generate_report") as span:
            span.set_attribute("llm.model", self._model)
            start = time.perf_counter()

            try:
                response = self._client.chat.completions.parse(
                    model=self._model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an expert Kubernetes SRE. "
                                "Return only the requested structured report."
                            ),
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    response_format=AIReport,
                )

                LLM_REQUESTS.labels(status="success").inc()

                if response.usage:
                    LLM_TOKENS.observe(response.usage.total_tokens)

                    span.set_attribute("llm.tokens.input", response.usage.prompt_tokens)
                    span.set_attribute(
                        "llm.tokens.output", response.usage.completion_tokens
                    )
                    span.set_attribute("llm.tokens.total", response.usage.total_tokens)

            except Exception as exc:  # noqa: BLE001
                span.record_exception(exc)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc)))

                logger.error("llm_response_failed", reason=repr(exc))
                LLM_REQUESTS.labels(status="error").inc()

                return AIReport(summary="AI analysis could not be completed.")

            finally:
                LLM_DURATION.observe(time.perf_counter() - start)

        report: AIReport | None = response.choices[0].message.parsed
        if report is None:
            logger.error("llm_response_empty", response=response)

            return AIReport(
                summary="AI analysis could not be completed.",
            )

        return report

    def is_server_reachable(self) -> bool:
        """Return True if the OpenAI API is reachable and responding."""

        try:
            self._client.models.list(timeout=2.0)
            return True

        except APIConnectionError:
            return False

        except APIStatusError:
            return True
