import argparse
import json

import structlog

from kubesage.bootstrap import create_analysis_service
from kubesage.database.session import SessionLocal
from kubesage.models.ai_report import AIReport

logger = structlog.get_logger(__name__)


def analyze_command(args: argparse.Namespace) -> None:
    """Manage the execution of the analyze command."""

    try:
        with SessionLocal() as db:
            analysis_service = create_analysis_service(db)
            analysis = analysis_service.analyze(namespace=args.namespace, pod=args.pod)
    except Exception as exc:
        logger.exception(exc)
        raise

    if analysis.report is None:
        analysis.report = AIReport(
            summary="AI analysis could not produce a report.",
        )

    print(json.dumps(analysis.report.model_dump(), indent=4, ensure_ascii=False))
