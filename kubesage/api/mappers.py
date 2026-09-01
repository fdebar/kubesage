from kubesage.api.schemas.analysis import AIReportResponse


def to_response(report: dict) -> AIReportResponse:
    return AIReportResponse(
        summary=report.get("summary", ""),
        root_cause=report.get("root_cause", ""),
        confidence=report.get("confidence", ""),
        impact=report.get("impact", ""),
        findings=report.get("findings", []),
        evidence=report.get("evidence", []),
        recommendations=report.get("recommendations", []),
        additional_investigations=report.get("additional_investigations", []),
    )
