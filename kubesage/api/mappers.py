from kubesage.api.schemas.response import AnalyzeResponse


def to_response(report: dict) -> AnalyzeResponse:
    return AnalyzeResponse(
        summary=report.get("summary", ""),
        root_cause=report.get("root_cause", ""),
        confidence=report.get("confidence", ""),
        impact=report.get("impact", ""),
        evidence=report.get("evidence", []),
        recommendations=report.get("recommendations", []),
        additional_investigations=report.get("additional_investigations", []),
    )
