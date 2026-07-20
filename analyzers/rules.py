from models.incident import Incident


def analyze_incident(incident: Incident) -> list[str]:

    findings = []

    for container in incident.containers:

        if container.restart_count > 3:
            findings.append(
                f"{container.name} a redémarré {container.restart_count} fois."
            )

        if container.waiting_reason == "CrashLoopBackOff":
            findings.append(
                "Le pod est en CrashLoopBackOff."
            )

        if container.last_exit_code == 137:
            findings.append(
                "OOMKilled probable."
            )

        if container.last_exit_code == 1:
            findings.append(
                "Le processus est sorti avec le code 1."
            )

    logs = incident.logs.lower()

    if "connection refused" in logs:
        findings.append(
            "Connexion refusée vers une dépendance."
        )

    if "redis" in logs:
        findings.append(
            "Redis apparaît dans les logs."
        )

    if "database" in logs:
        findings.append(
            "La base de données apparaît dans les logs."
        )

    return findings