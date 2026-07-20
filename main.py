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

report = service.analyze(
    args.namespace,
    args.pod,
)

print(report.to_json())
