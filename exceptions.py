import sys
from rich.console import Console
from rich.panel import Panel

console = Console()


class KubeSageException(Exception):

    def __init__(self):
        pass

    def throw_and_exit(exc: Exception, color: str = "bold red"):
        console.print(
            Panel(
                f"[bold {color}]{type(exc).__name__}:[/bold {color}] {exc}",
                title=f"[bold white on {color}] ERROR [/bold white on {color}]",
                border_style=color,
                expand=False,
            )
        )
        sys.exit(1)

    def throw_and_continue(exc: Exception, color: str = "bold yellow"):
        console.print(
            Panel(
                f"[bold {color}]{type(exc).__name__}:[/bold {color}] {exc}",
                title=f"[bold white on {color}] WARNING [/bold white on {color}]",
                border_style=color,
                expand=False,
            )
        )
