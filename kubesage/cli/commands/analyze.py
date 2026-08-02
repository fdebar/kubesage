import argparse
import json
import sys

from kubesage.bootstrap import create_incident_service
from kubesage.database.session import SessionLocal
from kubesage.observability import get_logger
from kubesage.utils.exceptions import KubeSageError


def analyze_command(args: argparse.Namespace) -> None:
    """Manage the execution of the analyze command."""

    with SessionLocal() as db:
        service = create_incident_service(db)

    try:
        analysis = service.analyze(namespace=args.namespace, pod=args.pod)
    except KubeSageError as exc:
        logger = get_logger(__name__)
        logger.error(exc)
        sys.exit(1)

    print(json.dumps(analysis.report.model_dump(), indent=4, ensure_ascii=False))
