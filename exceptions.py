import sys
from rich.console import Console
from rich.panel import Panel

console = Console()


class KubeSageException(Exception):

    def __init__(self) -> None:
        pass

    @staticmethod
    def throw_and_exit(exc: Exception | str, color: str = "bold red") -> None:
        exc_type = type(exc).__name__ if isinstance(exc, Exception) else "Error"
        console.print(
            Panel(
                f"[bold {color}]{exc_type}:[/bold {color}] {exc}",
                title=f"[bold white on {color}] ERROR [/bold white on {color}]",
                border_style=color,
                expand=False,
            )
        )
        sys.exit(1)

    @staticmethod
    def throw_and_continue(exc: Exception | str, color: str = "bold yellow") -> None:
        exc_type = type(exc).__name__ if isinstance(exc, Exception) else "Warning"
        console.print(
            Panel(
                f"[bold {color}]{exc_type}:[/bold {color}] {exc}",
                title=f"[bold white on {color}] WARNING [/bold white on {color}]",
                border_style=color,
                expand=False,
            )
        )
