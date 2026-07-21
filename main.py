import argparse
from commands.analyze import analyze_command
from commands.rules import rules_command


def main():
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
