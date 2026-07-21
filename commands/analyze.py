import json
from services.incident_service import IncidentService
from services.prometheus_service import PrometheusService

import argparse

def analyze_command(args: argparse.Namespace) -> None:
    """Manage the execution of the analyze command."""

    service = IncidentService()
    report = service.analyze(namespace=args.namespace, pod=args.pod)

    print(json.dumps(report, indent=4, ensure_ascii=False))
