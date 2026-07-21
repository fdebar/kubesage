from models.incident import Incident
from models.finding import Finding


def build_prompt(incident: Incident, findings: list[Finding], template: str):

    findings_text = "\n".join(
        [
            f"""
Severity:
{f.severity}

Title:
{f.title}

Description:
{f.description}

Confidence:
{f.confidence}

Source:
{f.source}
"""
            for f in findings
        ]
    )

    return f"""
{template}


Incident:

Namespace:
{incident.namespace}

Pod:
{incident.pod}

Phase:
{incident.phase}

Metrics
{incident.metrics}

Logs:
{incident.logs}

Diagnostics automatiques:
{findings_text}

"""
