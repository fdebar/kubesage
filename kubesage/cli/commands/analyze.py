import argparse
import json
import sys

import structlog

from kubesage.bootstrap import create_incident_service
from kubesage.database.session import SessionLocal
from kubesage.models.ai_report import AIReport
from kubesage.repositories.analysis_repository import AnalysisRepository
from kubesage.services.analysis_service import AnalysisService
from kubesage.utils.exceptions import KubeSageError

logger = structlog.get_logger(__name__)


def analyze_command(args: argparse.Namespace) -> None:
    """Manage the execution of the analyze command."""

    with SessionLocal() as db:
        incident_service = create_incident_service()

    try:
        analysis_service = AnalysisService(
            incident_service=incident_service,
            repository=AnalysisRepository(db),
        )
        analysis = analysis_service.analyze(namespace=args.namespace, pod=args.pod)
    except KubeSageError as exc:
        logger.exception(exc)
        sys.exit(1)

    if analysis.report is None:
        analysis.report = AIReport(
            summary="AI analysis could not produce a report.",
        )

    print(json.dumps(analysis.report.model_dump(), indent=4, ensure_ascii=False))
