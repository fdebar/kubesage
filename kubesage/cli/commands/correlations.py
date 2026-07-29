import argparse

from kubesage.analyzers.engine import DiagnosticEngine


def correlations_command(args: argparse.Namespace) -> None:
    """Manage the execution of the correlations command."""

    engine = DiagnosticEngine()
    if args.list:
        engine.list_correlations()
    else:
        print("No action specified for 'correlations'. Use --list.")
