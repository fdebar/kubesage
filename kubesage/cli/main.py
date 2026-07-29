import argparse
import uuid
from argparse import _SubParsersAction

from kubesage.cli.commands.analyze import analyze_command
from kubesage.cli.commands.correlations import correlations_command
from kubesage.cli.commands.rules import rules_command
from kubesage.observability import setup_logging
from kubesage.observability.context import set_request_id


def main() -> None:
    setup_logging()
    request_id = str(uuid.uuid4())
    set_request_id(request_id)

    parser = argparse.ArgumentParser(description="Incident analysis tool")
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    add_analyze_command(subparsers)
    add_correlations_command(subparsers)
    add_rules_command(subparsers)

    args = parser.parse_args()

    args.func(args)


def add_correlations_command(subparsers: _SubParsersAction) -> None:
    parser_correlations = subparsers.add_parser(
        "correlations", help="Manage correlations"
    )
    parser_correlations.add_argument(
        "--list",
        action="store_true",
        help="List all configured correlations",
        required=True,
    )
    parser_correlations.set_defaults(func=correlations_command)


def add_rules_command(subparsers: _SubParsersAction) -> None:
    parser_rules = subparsers.add_parser("rules", help="Manage rules")
    parser_rules.add_argument(
        "--list", action="store_true", help="List all configured rules", required=True
    )
    parser_rules.set_defaults(func=rules_command)


def add_analyze_command(subparsers: _SubParsersAction) -> None:
    parser_analyze = subparsers.add_parser("analyze", help="Analyzes an incident")
    parser_analyze.add_argument("--namespace", default="default")
    parser_analyze.add_argument("--pod", required=True)
    parser_analyze.set_defaults(func=analyze_command)


if __name__ == "__main__":
    main()
