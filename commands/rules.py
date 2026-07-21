from analyzers.engine import DiagnosticEngine


def rules_command(args):
    """Manage the execution of the rules command."""

    engine = DiagnosticEngine()
    if args.list:
        engine.list_rules()
    else:
        print("No action specified for 'rules'. Use --list.")
