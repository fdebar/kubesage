from dataclasses import dataclass

from opentelemetry import trace


@dataclass(frozen=True)
class TraceContext:
    trace_id: str | None
    span_id: str | None


def current_trace_context() -> TraceContext:
    span = trace.get_current_span()
    ctx = span.get_span_context()

    if not ctx.is_valid:
        return TraceContext(None, None)

    return TraceContext(
        trace_id=format(ctx.trace_id, "032x"),
        span_id=format(ctx.span_id, "016x"),
    )
