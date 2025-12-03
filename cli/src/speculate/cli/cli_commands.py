"""
Command implementations for speculate CLI.

Each command is a function with a docstring that serves as CLI help.
Only copier is lazy-imported (it's a large package).
"""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any, cast

import yaml
from prettyfmt import fmt_count_items, fmt_size_human
from rich import print as rprint
from strif import atomic_output_file

from speculate.cli.cli_ui import (
    print_cancelled,
    print_detail,
    print_error,
    print_error_item,
    print_header,
    print_info,
    print_missing,
    print_note,
    print_success,
    print_warning,
)


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file and return a dictionary."""
    with open(path) as f:
        result = yaml.safe_load(f)
    return cast(dict[str, Any], result) if isinstance(result, dict) else {}


def init(
    destination: str = ".",
    overwrite: bool = False,
    template: str = "gh:jlevy/speculate",
) -> None:
    """Initialize docs in a project using Copier.

    Copies the docs/ directory from the speculate template into your project.
    Creates a .copier-answers.yml file for future updates.

    Examples:
      speculate init              # Initialize in current directory
      speculate init ./my-project # Initialize in specific directory
      speculate init --overwrite  # Overwrite without confirmation
    """
    import copier  # Lazy import - large package

    dst = Path(destination).resolve()
    docs_path = dst / "docs"

    print_header("Initializing Speculate docs in:", dst)

    if docs_path.exists() and not overwrite:
        print_note(
            f"{docs_path} already exists", "Use `speculate update` to preserve local changes."
        )
        response = input("Reinitialize anyway? [y/N] ").strip().lower()
        if response != "y":
            print_cancelled()
            raise SystemExit(0)

    print_header("Docs will be copied to:", f"{docs_path}/")

    if not overwrite:
        response = input("Proceed? [Y/n] ").strip().lower()
        if response == "n":
            print_cancelled()
            raise SystemExit(0)

    rprint()
    _ = copier.run_copy(template, str(dst), overwrite=overwrite, defaults=overwrite)

    # Copy development.sample.md to development.md if it doesn't exist
    sample_dev_md = dst / "docs" / "project" / "development.sample.md"
    dev_md = dst / "docs" / "development.md"
    if sample_dev_md.exists() and not dev_md.exists():
        shutil.copy(sample_dev_md, dev_md)
        print_success("Created docs/development.md from template")

    # Show summary of what was created
    file_count, total_size = _get_dir_stats(docs_path)
    rprint()
    print_success(
        f"Docs installed ({fmt_count_items(file_count, 'file')}, {fmt_size_human(total_size)})"
    )
    rprint()

    # Automatically run install to set up tool configs
    install()

    # Remind user about required project-specific setup
    rprint("[bold yellow]Required next step:[/bold yellow]")
    print_detail("Customize docs/development.md with your project-specific setup.")
    rprint()
    rprint("Other commands:")
    print_detail("speculate status     # Check current status")
    print_detail("speculate update     # Pull future updates")
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
        print_error(
            "No .copier-answers.yml found", "Run `speculate init` first to initialize docs."
        )
        raise SystemExit(1)

    print_header("Updating docs from upstream template...", cwd)

    _ = copier.run_update(str(cwd), conflict="inline")

    rprint()
    print_success("Docs updated successfully!")
    rprint()

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
        print_error(
            "No docs/ directory found",
            "Run `speculate init` first, or manually copy docs/ to this directory.",
        )
        raise SystemExit(1)

    print_header("Installing tool configurations...", cwd)

    # .speculate/settings.yml — track install metadata
    _update_speculate_settings(cwd)

    # CLAUDE.md — ensure speculate header at top (idempotent)
    _ensure_speculate_header(cwd / "CLAUDE.md")

    # AGENTS.md — ensure speculate header at top (idempotent)
    _ensure_speculate_header(cwd / "AGENTS.md")

    # .cursor/rules/
    _setup_cursor_rules(cwd, include=include, exclude=exclude)

    rprint()
    print_success("Tool configs installed!")
    rprint()


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

    print_header("Speculate Status", cwd)

    # Check .copier-answers.yml
    answers_file = cwd / ".copier-answers.yml"
    if answers_file.exists():
        answers = _load_yaml(answers_file)
        commit = answers.get("_commit", "unknown")
        src = answers.get("_src_path", "unknown")
        print_success(f"Template version: {commit}")
        print_detail(f"Source: {src}")
    else:
        print_missing("No .copier-answers.yml (not initialized)")

    # Check .speculate/settings.yml
    settings_file = cwd / ".speculate" / "settings.yml"
    if settings_file.exists():
        settings = _load_yaml(settings_file)
        last_update = settings.get("last_update", "unknown")
        cli_version = settings.get("last_cli_version", "unknown")
        print_success(f"Last install: {last_update} (CLI {cli_version})")
    else:
        print_info(".speculate/settings.yml not found")

    # Check docs/
    docs_path = cwd / "docs"
    if docs_path.exists():
        file_count, total_size = _get_dir_stats(docs_path)
        print_success(
            f"docs/ exists ({fmt_count_items(file_count, 'file')}, {fmt_size_human(total_size)})"
        )
    else:
        print_missing("docs/ not found")

    # Check development.md (required)
    dev_md = cwd / "docs" / "development.md"
    if dev_md.exists():
        print_success("docs/development.md exists")
    else:
        print_error_item(
            "docs/development.md missing (required!)",
            "Create this file using docs/project/development.sample.md as a template.",
        )
        has_errors = True

    # Check tool configs
    for name, path in [
        ("CLAUDE.md", cwd / "CLAUDE.md"),
        ("AGENTS.md", cwd / "AGENTS.md"),
        (".cursor/rules/", cwd / ".cursor" / "rules"),
    ]:
        if path.exists():
            print_success(f"{name} exists")
        else:
            print_info(f"{name} not configured")

    rprint()

    if has_errors:
        raise SystemExit(1)


# Helper functions


def _update_speculate_settings(project_root: Path) -> None:
    """Create or update .speculate/settings.yml with install metadata."""
    settings_dir = project_root / ".speculate"
    settings_dir.mkdir(parents=True, exist_ok=True)
    settings_file = settings_dir / "settings.yml"

    # Read existing settings
    settings: dict[str, Any] = _load_yaml(settings_file) if settings_file.exists() else {}

    # Update with current info
    settings["last_update"] = datetime.now(UTC).isoformat()
    try:
        settings["last_cli_version"] = version("speculate")
    except Exception:
        settings["last_cli_version"] = "unknown"

    # Get docs version from .copier-answers.yml if available
    answers_file = project_root / ".copier-answers.yml"
    if answers_file.exists():
        answers = _load_yaml(answers_file)
        settings["last_docs_version"] = answers.get("_commit", "unknown")

    with atomic_output_file(settings_file) as temp_path:
        Path(temp_path).write_text(yaml.dump(settings, default_flow_style=False))
    print_success("Updated .speculate/settings.yml")


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
            print_info(f"{path.name} already configured")
            return
        # Prepend header to existing content
        new_content = SPECULATE_HEADER + "\n\n" + content
        action = "Updated"
    else:
        new_content = SPECULATE_HEADER + "\n"
        action = "Created"

    with atomic_output_file(path) as temp_path:
        Path(temp_path).write_text(new_content)
    print_success(f"{action} {path.name}")


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
        print_warning("docs/general/agent-rules/ not found, skipping Cursor setup")
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

    msg = f"Linked {linked_count} rules to .cursor/rules/"
    if skipped_count:
        msg += f" ({skipped_count} skipped by pattern)"
    print_success(msg)
