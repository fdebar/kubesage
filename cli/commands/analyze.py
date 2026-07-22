from utils.exceptions import KubeSageError
import json
import sys
from utils.config import logger
from services.incident_service import IncidentService

import argparse


def analyze_command(args: argparse.Namespace) -> None:
    """Manage the execution of the analyze command."""

    service = IncidentService()
    try:
        report = service.analyze(namespace=args.namespace, pod=args.pod)
    except KubeSageError as exc:
        logger.error(exc)
        sys.exit(1)

    print(json.dumps(report, indent=4, ensure_ascii=False))
