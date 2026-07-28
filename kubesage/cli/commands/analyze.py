import argparse
import json
import sys

from kubesage.observability import get_logger
from kubesage.services.incident_service import IncidentService
from kubesage.utils.exceptions import KubeSageError


def analyze_command(args: argparse.Namespace) -> None:
    """Manage the execution of the analyze command."""

    service = IncidentService()
    try:
        report = service.analyze(namespace=args.namespace, pod=args.pod)
    except KubeSageError as exc:
        logger = get_logger(__name__)
        logger.error(exc)
        sys.exit(1)

    print(json.dumps(report.model_dump(), indent=4, ensure_ascii=False))
