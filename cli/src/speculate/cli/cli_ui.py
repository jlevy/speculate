"""
CLI output helpers for consistent formatting.

All user-facing output should go through these functions to ensure
consistent styling across the CLI.
"""

from __future__ import annotations

from pathlib import Path

from rich import print as rprint

# Standard indentation for continuation lines
_INDENT = "  "


def print_header(title: str, path: Path | str | None = None) -> None:
    """Print a section header with optional path on a new indented line."""
    rprint(f"\n[bold]{title}[/bold]")
    if path is not None:
        rprint(f"{_INDENT}{path}")
    rprint()


def print_success(message: str) -> None:
    """Print a success message with green checkmark."""
    rprint(f"[green]✔︎[/green] {message}")


def print_error(message: str, detail: str | None = None) -> None:
    """Print an error message with red label and optional detail line."""
    rprint(f"[red]Error:[/red] {message}")
    if detail:
        rprint(f"{_INDENT}{detail}")


def print_warning(message: str, detail: str | None = None) -> None:
    """Print a warning message with yellow label and optional detail line."""
    rprint(f"[yellow]Warning:[/yellow] {message}")
    if detail:
        rprint(f"{_INDENT}{detail}")


def print_note(message: str, detail: str | None = None) -> None:
    """Print a note message with yellow label and optional detail line."""
    rprint(f"[yellow]Note:[/yellow] {message}")
    if detail:
        rprint(f"{_INDENT}{detail}")


def print_missing(message: str) -> None:
    """Print a missing/not-found item with yellow X."""
    rprint(f"[yellow]✘[/yellow] {message}")


def print_error_item(message: str, detail: str | None = None) -> None:
    """Print an error item with red X and optional detail line."""
    rprint(f"[red]✘[/red] {message}")
    if detail:
        rprint(f"{_INDENT}{detail}")


def print_info(message: str) -> None:
    """Print an info/neutral message with dim circle."""
    rprint(f"[dim]○[/dim] {message}")


def print_detail(message: str) -> None:
    """Print an indented detail/continuation line."""
    rprint(f"{_INDENT}{message}")


def print_cancelled() -> None:
    """Print cancellation message."""
    rprint("[yellow]Cancelled[/yellow]")
