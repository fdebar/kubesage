import argparse

import structlog

logger = structlog.get_logger()


def watch_command(args: argparse.Namespace) -> None:
    """Manage the execution of the watch command."""

    logger.info("watcher_starting")
