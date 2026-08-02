import argparse
import json
import sys

from kubesage.bootstrap import create_incident_service
from kubesage.database.session import SessionLocal
from kubesage.models.ai_report import AIReport
from kubesage.observability import get_logger
from kubesage.services.analysis_service import AnalysisService
from kubesage.utils.exceptions import KubeSageError


def analyze_command(args: argparse.Namespace) -> None:
    """Manage the execution of the analyze command."""

    with SessionLocal() as db:
        incident_service = create_incident_service(db)

    try:
        analysis_service = AnalysisService(
            incident_service=incident_service,
            repository=incident_service.analysis_repository,
        )
        analysis = analysis_service.analyze(namespace=args.namespace, pod=args.pod)
    except KubeSageError as exc:
        logger = get_logger(__name__)
        logger.error(exc)
        sys.exit(1)

    if analysis.report is None:
        analysis.report = AIReport(
            summary="AI analysis could not produce a report.",
        )

    print(json.dumps(analysis.report.model_dump(), indent=4, ensure_ascii=False))
