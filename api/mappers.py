from api.schemas.response import AnalyzeResponse


def to_response(report) -> AnalyzeResponse:
    return AnalyzeResponse(
        summary=report.get("summary", ""),
        severity=report.get("severity", "Unknown"),
        root_cause=report.get("root_cause", ""),
        recommendations=report.get("recommendations", []),
        kubectl_commands=report.get("kubectl_commands", []),
    )
