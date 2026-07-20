import argparse
from services.incident_service import IncidentService


def parse_args():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--namespace",
        default="default",
    )

    parser.add_argument(
        "--pod",
        required=True,
    )

    return parser.parse_args()


args = parse_args()

service = IncidentService()

incidents, findings = service.analyze(
    args.namespace,
    args.pod,
)

for finding in findings:

    print(
        f"""
[{finding.severity}]

{finding.title}

{finding.description}

Confidence:
{finding.confidence}

Source:
{finding.source}
"""
    )
