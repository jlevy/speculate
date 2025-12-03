"""
The `speculate` command installs and syncs structured agent documentation
into Git-based projects for use with Cursor, Claude Code, Codex, etc.
"""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import version
from textwrap import dedent

from clideps.utils.readable_argparse import ReadableColorFormatter, get_readable_console_width
from rich import get_console
from rich import print as rprint

from speculate.cli.cli_commands import init, install, status, update
from speculate.cli.cli_ui import print_cancelled, print_error

APP_NAME = "speculate"
DESCRIPTION = "speculate: Install and sync agent documentation"

ALL_COMMANDS = [init, update, install, status]


def get_version_name() -> str:
    try:
        return f"{APP_NAME} v{version(APP_NAME)}"
    except Exception:
        return f"{APP_NAME} (unknown version)"


def get_short_help(func: object) -> str:
    """Extract the first paragraph from a function's docstring."""
    doc = getattr(func, "__doc__", None)
    if not doc or not isinstance(doc, str):
        return ""
    doc = doc.strip()
    paragraphs = [p.strip() for p in doc.split("\n\n") if p.strip()]
    if paragraphs:
        return " ".join(paragraphs[0].split())
    return ""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        formatter_class=ReadableColorFormatter,
        epilog=dedent((__doc__ or "") + "\n\n" + get_version_name()),
        description=DESCRIPTION,
    )
    parser.add_argument("--version", action="store_true", help="show version and exit")

    subparsers = parser.add_subparsers(dest="subcommand", required=False)

    for func in ALL_COMMANDS:
        command_name = func.__name__.replace("_", "-")
        subparser = subparsers.add_parser(
            command_name,
            help=get_short_help(func),
            description=func.__doc__,
            formatter_class=ReadableColorFormatter,
        )

        # Command-specific arguments
        if func is init:
            subparser.add_argument(
                "destination",
                nargs="?",
                default=".",
                help="target directory (default: current directory)",
            )
            subparser.add_argument(
                "--overwrite",
                action="store_true",
                help="skip confirmation prompts",
            )
            subparser.add_argument(
                "--template",
                default="gh:jlevy/speculate",
                help="template source (default: gh:jlevy/speculate)",
            )

        if func is install:
            subparser.add_argument(
                "--include",
                action="append",
                help="include only rules matching pattern (supports * and **)",
            )
            subparser.add_argument(
                "--exclude",
                action="append",
                help="exclude rules matching pattern (supports * and **)",
            )

    return parser


def main() -> None:
    get_console().width = get_readable_console_width()
    parser = build_parser()
    args = parser.parse_args()

    if args.version:
        rprint(get_version_name())
        return

    if not args.subcommand:
        parser.print_help()
        return

    subcommand = args.subcommand.replace("-", "_")

    try:
        if subcommand == "init":
            init(destination=args.destination, overwrite=args.overwrite, template=args.template)
        elif subcommand == "update":
            update()
        elif subcommand == "install":
            install(include=args.include, exclude=args.exclude)
        elif subcommand == "status":
            status()
        else:
            raise ValueError(f"Unknown subcommand: {subcommand}")
        sys.exit(0)
    except KeyboardInterrupt:
        rprint()
        print_cancelled()
        sys.exit(130)
    except SystemExit as e:
        sys.exit(e.code)
    except Exception as e:
        rprint()
        print_error(str(e))
        rprint()
        sys.exit(1)


if __name__ == "__main__":
    main()
