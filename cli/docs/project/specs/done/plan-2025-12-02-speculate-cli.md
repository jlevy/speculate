# Plan Spec: Speculate CLI

## Purpose

This is a technical design doc used for assembling full context for the Speculate CLI
tool and to plan its implementation, including architecture and all key technical
choices.

It should be updated during the planning process, then kept as a record for later
context once implementation is begun.

## Background

### The Problem

When developing with LLMs/agents (Cursor, Claude Code, Codex, Windsurf), teams need:

- **Shared context** across human developers and AI tools

- **Decomposed tasks** with clear, reusable instructions

- **Reduced context windows** for more reliable rule adherence

- **Consistent workflows** across multiple projects

Currently, there’s no good way to:

1. Install a standardized docs structure into existing projects

2. Keep docs in sync as the upstream template evolves

3. Configure multiple AI tools (Cursor, Claude Code, Codex) consistently

### The Solution

**Speculate** addresses this by:

1. Using [Copier](https://github.com/copier-org/copier) to manage template installation
   and updates

2. Providing a friendly CLI wrapper (similar to
   [uvinit](https://github.com/jlevy/uvinit))

3. Auto-generating tool-specific config files (`CLAUDE.md`, `AGENTS.md`,
   `.cursor/rules/`)

### Reference Implementations

**uvinit** ([github.com/jlevy/uvinit](https://github.com/jlevy/uvinit)):

- Wraps Copier with friendlier UX

- Uses `copier.run_copy()` programmatically

- Published to PyPI for `uvx` usage

- Key Copier API patterns:

  - `copier.run_copy(src_path, dst_path)` — copy template to destination

  - `copier.run_update(dst_path, conflict="inline")` — update from upstream

  - `.copier-answers.yml` — stores template source and version info

**CLI Pattern** (used in kpress and similar tools):

- `argparse` + `clideps.ReadableColorFormatter` for readable help

- Modern Python 3.11+ with full type annotations

- Key patterns (full code samples included below):

  - `get_short_help(func)` — extracts first paragraph from docstring for CLI help

  - `build_parser()` — builds argparse with subcommands from function list

  - Subcommand normalization: `args.subcommand.replace("-", "_")` for function lookup

  - Error handling with rich output and proper exit codes

### Current State

This repository (`speculate`) contains:

- `docs/general/agent-rules/` — Cross-project rules

- `docs/general/agent-shortcuts/` — Reusable shortcuts

- `docs/general/agent-guidelines/` — Guidelines and notes

- `docs/project/` — Project-specific templates (specs, architecture, research)

- `docs/docs-overview.md` — Documentation explaining the system

See `docs/docs-overview.md` for full documentation structure.

### Reference Code from uvinit

The key Copier integration from uvinit’s `copier_workflow.py`:

```python
from pathlib import Path
from typing import Any

import copier
import yaml

def read_copier_answers(project_path: Path) -> dict[str, Any]:
    """
    Read the copier answers file to extract project metadata.

    Sample answers file:
    _commit: v0.2.3
    _src_path: gh:jlevy/speculate
    package_name: my-project
    """
    answers_path = project_path / ".copier-answers.yml"

    if not answers_path.exists():
        raise ValueError(f"Answers file not found: {answers_path}")
    try:
        with open(answers_path) as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        return {}


def copy_template(src_path: str, dst_path: str) -> Path:
    """
    Create a new project using copier.
    """
    copier.run_copy(
        src_path=src_path,
        dst_path=dst_path,
    )
    return Path(dst_path)
```

The key point is that `copier.run_copy()` and `copier.run_update()` are the primary
APIs:

- `copier.run_copy(src_path, dst_path)` — copies template to destination

- `copier.run_update(dst_path, conflict="inline")` — updates from upstream with inline
  conflict markers

- Both can raise `copier.CopierAnswersInterrupt` on user cancellation

### Reference Code: CLI Structure Pattern

The CLI structure pattern (simplified for speculate):

```python
# Example CLI main pattern (cli_main.py)
import argparse
import sys
from importlib.metadata import version
from textwrap import dedent

from clideps.utils.readable_argparse import ReadableColorFormatter, get_readable_console_width
from rich import get_console
from rich import print as rprint

APP_NAME = "myapp"
DESCRIPTION = "myapp: Description here"
ALL_COMMANDS = [init, build, clean]  # List of command functions


def get_version_name() -> str:
    try:
        return f"{APP_NAME} v{version(APP_NAME)}"
    except Exception:
        return f"{APP_NAME} (unknown version)"


def get_short_help(func: object) -> str:
    """
    Extract the first paragraph from a function's docstring for short help.
    """
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
        # Add command-specific arguments here

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

    # Normalize subcommand to use underscores (matches function names)
    subcommand = args.subcommand.replace("-", "_")

    try:
        if subcommand == "init":
            init(...)
            sys.exit(0)
        # ... other commands
    except SystemExit as e:
        sys.exit(e.code)
    except Exception as e:
        rprint(f"[red]Error:[/red] {e}")
        sys.exit(1)
```

### Reference Code: Command Implementation Pattern

```python
# Example command implementations (cli_commands.py)
from __future__ import annotations
from pathlib import Path
from rich import print as rprint


def init(site_name: str = "My Site", base_dir: str = ".", force: bool = False) -> None:
    """Initialize a new site with starter content.

    Creates a new project directory with sample content.

    Examples:
      myapp init
      myapp init --site-name "My Blog"
      myapp init --overwrite
    """
    # Implementation here
    rprint(f"[green]✔︎[/green] Initialized successfully")


def clean(output_dir: str = "output") -> None:
    """Remove build outputs.

    Examples:
      myapp clean
    """
    import shutil
    p = Path(output_dir)
    if p.exists():
        shutil.rmtree(p)
        rprint(f"[green]✔︎[/green] Removed {p}")
```

**Key patterns:**

- Each command is a function with a docstring that serves as CLI help

- First paragraph of docstring becomes short help text

- Examples section in docstring shows usage

- Use rich `rprint()` for formatted output

- Use `[green]✔︎[/green]` for success markers

- Lazy imports inside functions keep CLI startup fast

## Summary of Task

Build **Speculate**, a Python CLI tool with these commands:

| Command | Description |
| --- | --- |
| `speculate init [destination]` | Install docs into a project using Copier |
| `speculate update` | Pull latest docs from upstream template |
| `speculate install` | Generate/update tool configs (CLAUDE.md, AGENTS.md, .cursor/rules) |
| `speculate uninstall` | Remove tool configs (preserves docs/) |
| `speculate status` | Show current template version and sync status |

### Key Design Decisions

1. **Keep `docs/` at repo root** — Allows manual copying without Copier

2. **CLI in `src/speculate/cli/`** — Follows standard CLI pattern, single pyproject.toml

3. **Use argparse + clideps** — Standard pattern for readable CLI help

4. **No Jinja templating** — Docs are copied verbatim (simpler than uvinit)

5. **Smart `skip_if_exists`** — Project-specific files created once, not overwritten

## Backward Compatibility

Not applicable — this is a new tool with no existing users.

## Stage 1: Planning Stage

### Minimum Viable Features

**Must Have:**

- [ ] `speculate init [destination]` — Copy docs into a project

  - Default destination is current directory

  - Preview files that will be created/modified

  - Confirm before proceeding

  - Create `.copier-answers.yml` for future updates

- [ ] `speculate update` — Update docs from template

  - Run `copier update` with smart merge

  - Show what changed

  - Handle conflicts with `--conflict inline`

- [ ] `speculate install` — Generate tool configs

  - Create/update `.speculate/settings.yml` with install metadata

  - Create/update `CLAUDE.md` pointing to docs

  - Create/update `AGENTS.md` pointing to docs

  - Create `.cursor/rules/` symlinks to docs/general/agent-rules/

- [ ] `speculate uninstall` — Remove tool configs (non-destructive)

  - Remove speculate header from CLAUDE.md and AGENTS.md (preserves other content)

  - Header pattern: lines matching `IMPORTANT: You MUST read .*development\.md.*`
    followed by `(This project uses Speculate project structure.)`

  - If file becomes empty after header removal, delete the file

  - Remove all `.mdc` symlinks from `.cursor/rules/` that point to speculate docs

  - Remove `.speculate/settings.yml` (but not `.speculate/copier-answers.yml`)

  - Does NOT remove `docs/` directory (use `rm -rf docs/` manually if needed)

  - Confirm before proceeding (unless `--force`)

- [ ] `speculate status` — Show current state

  - Template version from `.copier-answers.yml`

  - Last install info from `.speculate/settings.yml`

  - Whether docs/ exists

  - Which tool configs exist

**Not In Scope (for v1):**

- Custom template URLs (always uses this repo)

- Interactive questionnaire (no template variables)

- Windsurf configuration

- Documentation website

### Acceptance Criteria

1. User can run `uvx speculate init` in any Git repo to add docs

2. User can run `speculate update` to pull upstream changes

3. User can run `speculate install` to configure Cursor/Claude Code/Codex

4. User can run `speculate uninstall` to cleanly remove tool configs

5. All commands provide clear output and confirmations

6. Tool is published to PyPI and works with `uvx`

## Stage 2: Architecture Stage

### Repository Structure

The repository has two main parts:

- `docs/` — Template content (what gets copied to user projects)

- `cli/` — The speculate CLI tool (Python package)

```
speculate/                        # Repository root
├── copier.yml                    # Copier config (at root, references docs/)
├── docs/                         # Template content (copied to user projects)
│   ├── docs-overview.md
│   ├── general/
│   │   ├── agent-rules/         # Rule files (*.md)
│   │   ├── agent-shortcuts/     # Shortcut files (*.md)
│   │   └── agent-guidelines/    # Guidelines and notes
│   └── project/
│       ├── architecture/
│       ├── research/
│       ├── specs/
│       └── development.sample.md
├── cli/                          # The speculate CLI package
│   ├── pyproject.toml
│   ├── Makefile
│   ├── README.md
│   ├── src/
│   │   └── speculate/
│   │       ├── __init__.py
│   │       ├── py.typed
│   │       └── cli/
│   │           ├── __init__.py
│   │           ├── cli_main.py   # Main entry point (argparse)
│   │           └── cli_commands.py  # init, update, install, status
│   └── tests/
└── LICENSE
```

Note: The CLI is in `cli/` subdirectory with its own pyproject.toml.
The copier.yml at the repo root will only copy `docs/` to user projects (excluding cli/,
etc.).

### Key Dependencies

```toml
dependencies = [
    "copier>=9.4.0",        # Template management
    "clideps>=0.1.8",       # CLI utilities (ReadableColorFormatter)
    "rich>=14.0.0",         # Terminal output
    "pyyaml>=6.0",          # Read .copier-answers.yml
    "strif>=3.0.1",         # Atomic file operations (https://github.com/jlevy/strif)
    "prettyfmt>=0.4.1",     # Human-friendly formatting (https://github.com/jlevy/prettyfmt)
]
```

### Utility Libraries

**[strif](https://github.com/jlevy/strif)** — A tiny library of string, file, and object
utilities:

- `atomic_output_file(path)` — Context manager for atomic file writes (writes to temp
  file, then renames on success)

- Use this when writing CLAUDE.md, AGENTS.md to avoid partial/corrupt files

```python
from strif import atomic_output_file

# Atomic file writing - ensures file is complete or not written at all
with atomic_output_file("CLAUDE.md") as temp_path:
    Path(temp_path).write_text(content)
```

**[prettyfmt](https://github.com/jlevy/prettyfmt)** — A tiny library for beautiful
outputs:

- `fmt_size_human(bytes)` — Format bytes as human-readable ("11.4M")

- `fmt_path(path)` — Format paths nicely for display

- `fmt_count_items(n, word)` — “23 files” or “1 file”

```python
from prettyfmt import fmt_size_human, fmt_path, fmt_count_items

fmt_size_human(12000000)      # -> '11.4M'
fmt_path("/some/long/path")   # -> nicely formatted path
fmt_count_items(23, "file")   # -> '23 files'
fmt_count_items(1, "file")    # -> '1 file'
```

### copier.yml Configuration

This file goes at the **repository root** (not in cli/). It tells Copier what to copy
when users run `speculate init`.

```yaml
_min_copier_version: "9.4.0"

# Only copy docs/ directory - exclude everything else
_exclude:
  - "*"
  - ".*"
  - "!docs/"

# No _skip_if_exists needed:
# - User-created files (specs, architecture docs) don't exist in the template
# - Template files (template-*.md) should receive updates
# - Copier's 3-way merge handles conflicts if users modify template files

_message_after_copy: |
  Speculate docs installed!
  See docs/docs-overview.md for usage guide.
```

Key points:

- `_exclude` uses wildcards to exclude everything except `docs/`

- No `_skip_if_exists` is needed because user-created files don’t exist in the template

- Copier’s 3-way merge handles conflicts when users modify template files

- Only `docs/` directory gets copied to user projects

- `_message_after_copy` shows after successful copy

### CLI Module Design

Following the patterns above with modern Python 3.11+ types.

**cli_main.py** — Main entry point:

```python
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

from speculate.cli.cli_commands import init, install, status, uninstall, update

APP_NAME = "speculate"
DESCRIPTION = "speculate: Install and sync agent documentation"

ALL_COMMANDS = [init, update, install, uninstall, status]


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
                help="overwrite existing docs without confirmation",
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

        if func is uninstall:
            subparser.add_argument(
                "--force",
                action="store_true",
                help="skip confirmation prompt",
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
            init(destination=args.destination, force=args.force)
        elif subcommand == "update":
            update()
        elif subcommand == "install":
            install(include=args.include, exclude=args.exclude)
        elif subcommand == "uninstall":
            uninstall(force=args.force)
        elif subcommand == "status":
            status()
        else:
            raise ValueError(f"Unknown subcommand: {subcommand}")
        sys.exit(0)
    except KeyboardInterrupt:
        rprint("\n[yellow]Cancelled[/yellow]")
        sys.exit(130)
    except SystemExit as e:
        sys.exit(e.code)
    except Exception as e:
        rprint(f"\n[red]Error:[/red] {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**cli_commands.py** — Command implementations:

```python
"""
Command implementations for speculate CLI.

Each command is a function with a docstring that serves as CLI help.
Only copier is lazy-imported (it's a large package).
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import yaml
from prettyfmt import fmt_count_items, fmt_size_human
from rich import print as rprint
from strif import atomic_output_file

TEMPLATE = "gh:jlevy/speculate"


def init(destination: str = ".", force: bool = False) -> None:
    """Initialize docs in a project using Copier.

    Copies the docs/ directory from the speculate template into your project.
    Creates a .copier-answers.yml file for future updates.

    Examples:
      speculate init              # Initialize in current directory
      speculate init ./my-project # Initialize in specific directory
      speculate init --overwrite      # Overwrite without confirmation
    """
    import copier  # Lazy import - large package

    dst = Path(destination).resolve()
    docs_path = dst / "docs"

    rprint(f"\n[bold]Initializing Speculate docs in:[/bold] {dst}\n")

    if docs_path.exists() and not force:
        rprint(f"[yellow]Warning:[/yellow] {docs_path} already exists")
        response = input("Overwrite? [y/N] ").strip().lower()
        if response != "y":
            rprint("[yellow]Cancelled[/yellow]")
            raise SystemExit(0)

    rprint("[bold]Docs will be copied to:[/bold]")
    rprint(f"  {docs_path}/")
    rprint()

    if not force:
        response = input("Proceed? [Y/n] ").strip().lower()
        if response == "n":
            rprint("[yellow]Cancelled[/yellow]")
            raise SystemExit(0)

    rprint()
    copier.run_copy(TEMPLATE, str(dst))

    # Show summary of what was created
    file_count, total_size = _get_dir_stats(docs_path)
    rprint(f"\n[green]✔︎[/green] Docs installed ({fmt_count_items(file_count, 'file')}, {fmt_size_human(total_size)})\n")

    # Automatically run install to set up tool configs
    install()

    # Remind user about required project-specific setup
    rprint("[bold yellow]Required next step:[/bold yellow]")
    rprint("  Create docs/development.md with your project-specific setup.")
    rprint("  Use docs/development.sample.md as a template.")
    rprint()
    rprint("Other commands:")
    rprint("  speculate status     # Check current status")
    rprint("  speculate update     # Pull future updates")
    rprint()


def update() -> None:
    """Update docs from the upstream template.

    Pulls the latest changes from the speculate template and merges them
    with your local docs. Local customizations in docs/project/ are preserved.

    Automatically runs `install` after update to refresh tool configs.

    Examples:
      speculate update
    """
    import copier  # Lazy import - large package

    cwd = Path.cwd()
    answers_file = cwd / ".copier-answers.yml"

    if not answers_file.exists():
        rprint("[red]Error:[/red] No .copier-answers.yml found")
        rprint("Run `speculate init` first to initialize docs.")
        raise SystemExit(1)

    rprint("\n[bold]Updating docs from upstream template...[/bold]\n")

    copier.run_update(str(cwd), conflict="inline")

    rprint("\n[green]✔︎[/green] Docs updated successfully!\n")

    # Automatically run install to refresh tool configs
    install()


def install(
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> None:
    """Generate tool configs for Cursor, Claude Code, and Codex.

    Creates or updates:
      - .speculate/settings.yml (install metadata)
      - CLAUDE.md (for Claude Code) — adds speculate header if missing
      - AGENTS.md (for Codex) — adds speculate header if missing
      - .cursor/rules/ (symlinks for Cursor)

    This command is idempotent and can be run multiple times safely.
    It's automatically called by `init` and `update`.

    Supports include/exclude patterns with wildcards:
      - `*` matches any characters within a filename
      - `**` matches any path segments
      - Default: include all (["**/*.md"])

    Examples:
      speculate install
      speculate install --include "general-*.md"
      speculate install --exclude "convex-*.md"
    """
    cwd = Path.cwd()
    docs_path = cwd / "docs"

    if not docs_path.exists():
        rprint("[red]Error:[/red] No docs/ directory found")
        rprint("Run `speculate init` first, or manually copy docs/ to this directory.")
        raise SystemExit(1)

    rprint("\n[bold]Installing tool configurations...[/bold]\n")

    # .speculate/settings.yml — track install metadata
    _update_speculate_settings(cwd)

    # CLAUDE.md — ensure speculate header at top (idempotent)
    _ensure_speculate_header(cwd / "CLAUDE.md")

    # AGENTS.md — ensure speculate header at top (idempotent)
    _ensure_speculate_header(cwd / "AGENTS.md")

    # .cursor/rules/
    _setup_cursor_rules(cwd, include=include, exclude=exclude)

    rprint("\n[green]✔︎[/green] Tool configs installed!\n")


def status() -> None:
    """Show current template version and sync status.

    Displays:
      - Template version from .copier-answers.yml
      - Last install info from .speculate/settings.yml
      - Whether docs/ exists
      - Whether development.md exists (required)
      - Which tool configs are present

    Exits with error if development.md is missing (required project setup).

    Examples:
      speculate status
    """
    cwd = Path.cwd()
    has_errors = False

    rprint("\n[bold]Speculate Status[/bold]\n")

    # Check .copier-answers.yml
    answers_file = cwd / ".copier-answers.yml"
    if answers_file.exists():
        with open(answers_file) as f:
            answers = yaml.safe_load(f) or {}
        commit = answers.get("_commit", "unknown")
        src = answers.get("_src_path", "unknown")
        rprint(f"[green]✔︎[/green] Template version: {commit}")
        rprint(f"   Source: {src}")
    else:
        rprint("[yellow]✘[/yellow] No .copier-answers.yml (not initialized)")

    # Check .speculate/settings.yml
    settings_file = cwd / ".speculate" / "settings.yml"
    if settings_file.exists():
        with open(settings_file) as f:
            settings = yaml.safe_load(f) or {}
        last_update = settings.get("last_update", "unknown")
        cli_version = settings.get("last_cli_version", "unknown")
        rprint(f"[green]✔︎[/green] Last install: {last_update} (CLI {cli_version})")
    else:
        rprint("[dim]○[/dim] .speculate/settings.yml not found")

    # Check docs/
    docs_path = cwd / "docs"
    if docs_path.exists():
        file_count, total_size = _get_dir_stats(docs_path)
        rprint(f"[green]✔︎[/green] docs/ exists ({fmt_count_items(file_count, 'file')}, {fmt_size_human(total_size)})")
    else:
        rprint("[yellow]✘[/yellow] docs/ not found")

    # Check development.md (required)
    dev_md = cwd / "docs" / "development.md"
    if dev_md.exists():
        rprint(f"[green]✔︎[/green] docs/development.md exists")
    else:
        rprint("[red]✘[/red] docs/development.md missing (required!)")
        rprint("   Create this file using docs/development.sample.md as a template.")
        has_errors = True

    # Check tool configs
    for name, path in [
        ("CLAUDE.md", cwd / "CLAUDE.md"),
        ("AGENTS.md", cwd / "AGENTS.md"),
        (".cursor/rules/", cwd / ".cursor" / "rules"),
    ]:
        if path.exists():
            rprint(f"[green]✔︎[/green] {name} exists")
        else:
            rprint(f"[dim]○[/dim] {name} not configured")

    rprint()

    if has_errors:
        raise SystemExit(1)


def uninstall(force: bool = False) -> None:
    """Remove tool configs installed by speculate.

    Removes:
      - Speculate header from CLAUDE.md (preserves other content)
      - Speculate header from AGENTS.md (preserves other content)
      - .cursor/rules/*.mdc symlinks that point to speculate docs
      - .speculate/settings.yml

    Does NOT remove:
      - docs/ directory (remove manually if desired)
      - .speculate/copier-answers.yml (needed for `speculate update`)

    If CLAUDE.md or AGENTS.md becomes empty after header removal, the file
    is deleted entirely.

    Examples:
      speculate uninstall           # Uninstall with confirmation
      speculate uninstall --force   # Uninstall without confirmation
    """
    cwd = Path.cwd()

    rprint("\n[bold]Uninstalling Speculate tool configs...[/bold]\n")

    # Preview what will be removed
    changes: list[str] = []

    claude_md = cwd / "CLAUDE.md"
    if claude_md.exists() and SPECULATE_MARKER in claude_md.read_text():
        changes.append("Remove speculate header from CLAUDE.md")

    agents_md = cwd / "AGENTS.md"
    if agents_md.exists() and SPECULATE_MARKER in agents_md.read_text():
        changes.append("Remove speculate header from AGENTS.md")

    cursor_rules = cwd / ".cursor" / "rules"
    if cursor_rules.exists():
        symlinks = [f for f in cursor_rules.glob("*.mdc") if f.is_symlink()]
        if symlinks:
            changes.append(f"Remove {len(symlinks)} symlinks from .cursor/rules/")

    settings_file = cwd / ".speculate" / "settings.yml"
    if settings_file.exists():
        changes.append("Remove .speculate/settings.yml")

    if not changes:
        rprint("[dim]○[/dim] Nothing to uninstall")
        return

    rprint("[bold]Will perform:[/bold]")
    for change in changes:
        rprint(f"  - {change}")
    rprint()

    if not force:
        response = input("Proceed? [y/N] ").strip().lower()
        if response != "y":
            rprint("[yellow]Cancelled[/yellow]")
            raise SystemExit(0)

    rprint()

    # Remove speculate header from CLAUDE.md
    _remove_speculate_header(claude_md)

    # Remove speculate header from AGENTS.md
    _remove_speculate_header(agents_md)

    # Remove .cursor/rules/ symlinks
    _remove_cursor_rules(cwd)

    # Remove .speculate/settings.yml
    if settings_file.exists():
        settings_file.unlink()
        rprint("[green]✔︎[/green] Removed .speculate/settings.yml")

    rprint("\n[green]✔︎[/green] Uninstall complete!\n")
    rprint("[dim]Note: docs/ directory preserved. Remove manually if desired.[/dim]")
    rprint()


# Helper functions

def _update_speculate_settings(project_root: Path) -> None:
    """Create or update .speculate/settings.yml with install metadata."""
    settings_dir = project_root / ".speculate"
    settings_dir.mkdir(parents=True, exist_ok=True)
    settings_file = settings_dir / "settings.yml"

    # Read existing settings
    if settings_file.exists():
        with open(settings_file) as f:
            settings = yaml.safe_load(f) or {}
    else:
        settings = {}

    # Update with current info
    settings["last_update"] = datetime.now(timezone.utc).isoformat()
    try:
        settings["last_cli_version"] = version("speculate")
    except Exception:
        settings["last_cli_version"] = "unknown"

    # Get docs version from .copier-answers.yml if available
    answers_file = project_root / ".copier-answers.yml"
    if answers_file.exists():
        with open(answers_file) as f:
            answers = yaml.safe_load(f) or {}
        settings["last_docs_version"] = answers.get("_commit", "unknown")

    with atomic_output_file(settings_file) as temp_path:
        Path(temp_path).write_text(yaml.dump(settings, default_flow_style=False))
    rprint(f"[green]✔︎[/green] Updated .speculate/settings.yml")


def _get_dir_stats(path: Path) -> tuple[int, int]:
    """Return (file_count, total_bytes) for all files in a directory."""
    file_count = 0
    total_size = 0
    for f in path.rglob("*"):
        if f.is_file():
            file_count += 1
            total_size += f.stat().st_size
    return file_count, total_size


SPECULATE_MARKER = "Speculate project structure"
SPECULATE_HEADER = f"""IMPORTANT: You MUST read ./docs/development.md and ./docs/docs-overview.md for project documentation.
(This project uses {SPECULATE_MARKER}.)"""


def _ensure_speculate_header(path: Path) -> None:
    """Ensure SPECULATE_HEADER is at the top of the file (idempotent).

    If file exists and already has the marker, do nothing.
    If file exists without marker, prepend the header.
    If file doesn't exist, create with just the header.
    """
    if path.exists():
        content = path.read_text()
        if SPECULATE_MARKER in content:
            rprint(f"[dim]○[/dim] {path.name} already configured")
            return
        # Prepend header to existing content
        new_content = SPECULATE_HEADER + "\n\n" + content
        action = "Updated"
    else:
        new_content = SPECULATE_HEADER + "\n"
        action = "Created"

    with atomic_output_file(path) as temp_path:
        Path(temp_path).write_text(new_content)
    rprint(f"[green]✔︎[/green] {action} {path.name}")


def _matches_patterns(
    filename: str,
    include: list[str] | None,
    exclude: list[str] | None,
) -> bool:
    """Check if filename matches include patterns and doesn't match exclude patterns.

    Supports wildcards:
      - `*` matches any characters within a filename
      - `**` is treated same as `*` for simple filename matching

    Default behavior: include all if no include patterns specified.
    """
    import fnmatch

    # Normalize ** to * for fnmatch (which doesn't support **)
    def normalize(pattern: str) -> str:
        return pattern.replace("**", "*")

    # If include patterns specified, file must match at least one
    if include:
        if not any(fnmatch.fnmatch(filename, normalize(p)) for p in include):
            return False

    # If exclude patterns specified, file must not match any
    if exclude:
        if any(fnmatch.fnmatch(filename, normalize(p)) for p in exclude):
            return False

    return True


def _setup_cursor_rules(
    project_root: Path,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> None:
    """Set up .cursor/rules/ with symlinks to docs/general/agent-rules/.

    Note: Cursor requires .mdc extension, so we create symlinks with .mdc
    extension pointing to the source .md files.

    Supports include/exclude patterns for filtering which rules to link.
    """
    cursor_dir = project_root / ".cursor" / "rules"
    cursor_dir.mkdir(parents=True, exist_ok=True)

    rules_dir = project_root / "docs" / "general" / "agent-rules"
    if not rules_dir.exists():
        rprint("[yellow]Warning:[/yellow] docs/general/agent-rules/ not found, skipping Cursor setup")
        return

    linked_count = 0
    skipped_count = 0
    for rule_file in sorted(rules_dir.glob("*.md")):
        # Check include/exclude patterns
        if not _matches_patterns(rule_file.name, include, exclude):
            skipped_count += 1
            continue

        # Cursor requires .mdc extension
        link_name = rule_file.stem + ".mdc"
        link_path = cursor_dir / link_name
        if link_path.exists() or link_path.is_symlink():
            link_path.unlink()

        # Create relative symlink
        relative_target = Path("..") / ".." / "docs" / "general" / "agent-rules" / rule_file.name
        link_path.symlink_to(relative_target)
        linked_count += 1

    msg = f"[green]✔︎[/green] Linked {linked_count} rules to .cursor/rules/"
    if skipped_count:
        msg += f" ({skipped_count} skipped by pattern)"
    rprint(msg)


# Regex pattern to match the speculate header block
# Matches: "IMPORTANT: You MUST read ..." line + "(This project uses Speculate project structure.)" line
# Works wherever the header appears in the file (not just at the start)
# Handles trailing whitespace and blank lines after the header
SPECULATE_HEADER_PATTERN = re.compile(
    r"^IMPORTANT: You MUST read [^\n]*development\.md[^\n]*\n"
    r"\(This project uses Speculate project structure\.\)[ \t]*\n*",
    re.MULTILINE,
)


def _remove_speculate_header(path: Path) -> None:
    """Remove the speculate header from a file (non-destructive).

    If the file contains the speculate header pattern, removes it.
    If the file becomes empty after removal, deletes the file.
    If the file doesn't exist or has no header, does nothing.
    """
    if not path.exists():
        return

    content = path.read_text()
    if SPECULATE_MARKER not in content:
        return

    # Remove the header using regex
    new_content = SPECULATE_HEADER_PATTERN.sub("", content)

    # Check if file is now empty (or just whitespace)
    if not new_content.strip():
        path.unlink()
        rprint(f"[green]✔︎[/green] Removed {path.name} (was empty after header removal)")
    else:
        with atomic_output_file(path) as temp_path:
            Path(temp_path).write_text(new_content)
        rprint(f"[green]✔︎[/green] Removed speculate header from {path.name}")


def _remove_cursor_rules(project_root: Path) -> None:
    """Remove .cursor/rules/*.mdc symlinks that point to speculate docs.

    Only removes symlinks, not regular files. Also removes broken symlinks.
    """
    cursor_dir = project_root / ".cursor" / "rules"
    if not cursor_dir.exists():
        return

    removed_count = 0
    for link_path in cursor_dir.glob("*.mdc"):
        if link_path.is_symlink():
            # Check if it points to our docs (or is broken)
            try:
                target = link_path.resolve()
                # Remove if it points to docs/general/agent-rules/ or is broken
                if "docs/general/agent-rules" in str(target) or not target.exists():
                    link_path.unlink()
                    removed_count += 1
            except OSError:
                # Broken symlink, remove it
                link_path.unlink()
                removed_count += 1

    if removed_count > 0:
        rprint(f"[green]✔︎[/green] Removed {removed_count} symlinks from .cursor/rules/")
```

### pyproject.toml Updates

The current `cli/pyproject.toml` already has the correct structure.
Update these sections:

```toml
[project]
name = "speculate"
description = "Install and sync agent documentation for Cursor, Claude Code, Codex"

# Dependencies:
dependencies = [
    "copier>=9.4.0",
    "clideps>=0.1.8",
    "rich>=14.0.0",
    "pyyaml>=6.0",
    "strif>=3.0.1",
    "prettyfmt>=0.4.1",
]

[project.scripts]
# Change from "speculate:main" to:
speculate = "speculate.cli.cli_main:main"

# Already correct:
[tool.hatch.build.targets.wheel]
packages = ["src/speculate"]
```

Note: The current pyproject.toml has `speculate = "speculate:main"` which points to a
placeholder. This should be changed to `speculate.cli.cli_main:main` once the CLI module
is created.

### Workflow Diagrams

**Init Flow:**

```
speculate init [destination]
    │
    ├─► Check if docs/ already exists
    │       └─► If yes and not --overwrite, confirm overwrite
    │
    ├─► Preview files to be created
    │
    ├─► Confirm with user (unless --overwrite)
    │
    ├─► copier.run_copy(TEMPLATE, destination)
    │
    └─► Print next steps
```

**Update Flow:**

```
speculate update
    │
    ├─► Check .copier-answers.yml exists
    │       └─► If not, error: "Run speculate init first"
    │
    ├─► copier.run_update(".", conflict="inline")
    │       └─► Smart 3-way merge preserves local changes
    │
    └─► Show success message
```

**Install Flow:**

```
speculate install
    │
    ├─► Check docs/ exists
    │       └─► If not, error: "Run speculate init first"
    │
    ├─► Generate/write CLAUDE.md
    │
    ├─► Generate/write AGENTS.md
    │
    └─► Create .cursor/rules/ symlinks
```

## Stage 3: Refine Architecture

### Reusable Patterns

The code samples above (CLI Structure Pattern, Command Implementation Pattern, Copier
integration) provide all patterns needed.
Key components:

| Component | Description |
| --- | --- |
| CLI main pattern | argparse + subcommands with `ReadableColorFormatter` |
| Command pattern | Functions with docstrings as CLI help |
| Error handling | try/except with rich output and exit codes |
| Copier integration | `copier.run_copy()` and `copier.run_update()` |
| Status reading | Parse `.copier-answers.yml` with pyyaml |

### Copier API Reference

The Copier library provides these key functions (from `copier` package):

```python
import copier

# Copy a template to a destination
# src_path can be: "gh:user/repo", local path, or URL
# Creates .copier-answers.yml in destination
copier.run_copy(
    src_path="gh:jlevy/speculate",
    dst_path="/path/to/project",
    # Optional: user_defaults={"key": "value"},
    # Optional: answers_file="path/to/answers.yml",
)

# Update from upstream template
# Reads .copier-answers.yml to find source
# conflict="inline" adds conflict markers instead of failing
copier.run_update(
    dst_path="/path/to/project",
    conflict="inline",
)

# Both functions can raise:
# - copier.CopierAnswersInterrupt — user cancelled during prompts
# - Various exceptions for network/file errors
```

The `.copier-answers.yml` file format:

```yaml
# Auto-generated by copier
_commit: v0.2.3 # Git tag/commit of template
_src_path: gh:jlevy/speculate # Template source
# Any template variables would appear here
```

### Simplifications (Code Saved)

1. **No template variables** — uvinit prompts for project name, author, etc.
   We skip this entirely since docs are copied verbatim.
   Saves ~100 lines of questionnaire code.

2. **No git setup** — uvinit helps create GitHub repos.
   We assume project already has git.
   Saves ~200 lines of git workflow code.

3. **Single template source** — Always uses `gh:jlevy/speculate`. No `--template`
   argument needed.

4. **No GitHub integration** — uvinit has GitHub API calls.
   We don’t need any.

5. **No questionary prompts** — uvinit uses questionary for interactive prompts.
   We use simple `input()` for the few confirmations needed.

### Files to Create/Modify

| File | Action | Description |
| --- | --- | --- |
| `copier.yml` | Create | Copier configuration (at repo root) |
| `cli/pyproject.toml` | Modify | Add dependencies, update entry point |
| `cli/src/speculate/__init__.py` | Update | Export main function |
| `cli/src/speculate/cli/__init__.py` | Create | CLI package init |
| `cli/src/speculate/cli/cli_main.py` | Create | Main entry point with argparse |
| `cli/src/speculate/cli/cli_commands.py` | Create | Command implementations |
| `cli/README.md` | Update | Add Speculate usage |

## Resolved Decisions

These decisions were made during spec review:

| # | Decision | Resolution |
| --- | --- | --- |
| 1 | Project name | `speculate` (used everywhere) |
| 2 | Initial version | `v0.1.0` |
| 3 | Template source | `gh:jlevy/speculate` |
| 4 | Cursor file extension | `.mdc` (symlinks to `.md` source files) |
| 5 | File reference syntax | `@` prefix for consistency (e.g., `@docs/...`) |
| 6 | Windows symlinks | Ignored for v1 (document as limitation) |
| 7 | Command chaining | `init` and `update` both call `install` automatically |
| 8 | Install without init | Yes, just requires `docs/` directory to exist |
| 9 | Include/exclude patterns | Supported with `*` and `**` wildcards |
| 10 | development.md | Required; `status` exits with error if missing |
| 11 | CLAUDE.md/AGENTS.md | Idempotent header prepend (checks for "Speculate project structure") |
| 12 | Uninstall behavior | Non-destructive: removes header via regex, preserves other content, deletes file only if empty |
| 13 | Uninstall scope | Removes tool configs only; does NOT remove docs/ or .speculate/copier-answers.yml |

### Key Implementation Notes

1. **Cursor requires .mdc extension** — The `_setup_cursor_rules()` function creates
   symlinks with `.mdc` extension pointing to the source `.md` files.

2. **development.md is required** — After `init`, users must create
   `docs/development.md` using `development.sample.md` as a template.
   `speculate status` will error if this file is missing.

3. **CLAUDE.md and AGENTS.md are idempotent** — The `install` command adds a single
   header line at the top of existing files.
   It checks for “Speculate project structure” to avoid duplicate headers.

4. **Include/exclude patterns** — Use `--include` and `--exclude` flags with `install`
   to filter which rules are linked to `.cursor/rules/`.

5. **Uninstall is non-destructive** — The `uninstall` command removes only the speculate
   header from CLAUDE.md and AGENTS.md (preserving other content), removes
   .cursor/rules/ symlinks, and removes .speculate/settings.yml.
   It does NOT remove docs/ or .speculate/copier-answers.yml.
   Uses regex pattern to match header precisely:
   `^IMPORTANT: You MUST read .*development\.md.*\n\(This project uses Speculate project structure\.\)\n*`

* * *

**Next Step:** Create implementation spec at
[impl-2025-12-02-speculate-cli.md](impl-2025-12-02-speculate-cli.md) for Stage 3
(Implementation) with detailed phases and tasks.
