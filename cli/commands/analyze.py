from observability import get_logger
from utils.exceptions import KubeSageError
from services.incident_service import IncidentService
import argparse
import json
import sys


def analyze_command(args: argparse.Namespace) -> None:
    """Manage the execution of the analyze command."""

    service = IncidentService()
    try:
        report = service.analyze(namespace=args.namespace, pod=args.pod)
    except KubeSageError as exc:
        logger = get_logger(__name__)
        logger.error(exc)
        sys.exit(1)

    print(json.dumps(report, indent=4, ensure_ascii=False))
