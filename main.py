from services.incident_service import IncidentService


def main():

    service = IncidentService()

    incident, findings = service.analyze(
        namespace="default",
        pod="ai-demo-app",
    )

    print("=" * 60)

    print(f"Pod        : {incident.pod}")
    print(f"Namespace  : {incident.namespace}")
    print(f"Phase      : {incident.phase}")

    print()

    print("Containers")

    for c in incident.containers:

        print(
            f"- {c.name}"
            f" ready={c.ready}"
            f" restart={c.restart_count}"
            f" waiting={c.waiting_reason}"
        )

    print()

    print("Findings")

    for finding in findings:
        print(f"• {finding}")

    print()

    print("Warnings")

    for event in incident.events:
        print(f"- {event['reason']} : {event['message']}")


if __name__ == "__main__":
    main()