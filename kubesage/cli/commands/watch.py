import argparse

import structlog

from kubesage.worker.main import run_worker

logger = structlog.get_logger()


def watch_command(args: argparse.Namespace) -> None:
    """
    Start Kubernetes watcher.
    """

    run_worker()
