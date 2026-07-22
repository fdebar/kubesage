import argparse
from cli.commands.analyze import analyze_command
from cli.commands.rules import rules_command
from observability import setup_logging
import uuid
from observability.context import set_request_id


def main() -> None:
    setup_logging()
    request_id = str(uuid.uuid4())
    set_request_id(request_id)

    parser = argparse.ArgumentParser(description="Incident analysis tool")

    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    parser_analyze = subparsers.add_parser(
        "analyze", help="Analyzes an incident on a specific pod"
    )
    parser_analyze.add_argument("--namespace", default="default")
    parser_analyze.add_argument("--pod", required=True)
    parser_analyze.set_defaults(func=analyze_command)

    parser_rules = subparsers.add_parser("rules", help="Manage rules")
    parser_rules.add_argument(
        "--list", action="store_true", help="List all configured rules", required=True
    )
    parser_rules.set_defaults(func=rules_command)

    args = parser.parse_args()

    args.func(args)


if __name__ == "__main__":
    main()
