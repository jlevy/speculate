"""
Command implementations for speculate CLI.

Each command is a function with a docstring that serves as CLI help.
Only copier is lazy-imported (it's a large package).
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import UTC, datetime
from importlib.metadata import version
from importlib.resources import files
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


# Package name for version lookup (PyPI package name)
PACKAGE_NAME = "speculate-cli"

# Speculate configuration paths (all under .speculate/)
SPECULATE_DIR = ".speculate"
COPIER_ANSWERS_FILE = f"{SPECULATE_DIR}/copier-answers.yml"
SETTINGS_FILE = f"{SPECULATE_DIR}/settings.yml"


def init(
    destination: str = ".",
    overwrite: bool = False,
    template: str = "gh:jlevy/speculate",
    ref: str = "HEAD",
) -> None:
    """Initialize docs in a project using Copier.

    Copies the docs/ directory from the speculate template into your project.
    Creates .speculate/copier-answers.yml for future updates.

    By default, always pulls from the latest commit (HEAD) so docs updates
    don't require new CLI releases. Use --ref to update to a specific version.

    Examples:
      speculate init              # Initialize in current directory
      speculate init ./my-project # Initialize in specific directory
      speculate init --overwrite  # Overwrite without confirmation
      speculate init --ref v1.0.0 # Use specific tag/commit
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
    # vcs_ref=HEAD ensures we always get latest docs without needing CLI releases
    _ = copier.run_copy(template, str(dst), overwrite=overwrite, defaults=overwrite, vcs_ref=ref)

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
    answers_file = cwd / COPIER_ANSWERS_FILE

    if not answers_file.exists():
        print_error(
            f"No {COPIER_ANSWERS_FILE} found",
            "Run `speculate init` first to initialize docs.",
        )
        raise SystemExit(1)

    print_header("Updating docs from upstream template...", cwd)

    try:
        _ = copier.run_update(
            str(cwd),
            answers_file=COPIER_ANSWERS_FILE,
            conflict="inline",
            overwrite=True,  # Required to update subprojects
        )
    except Exception as e:
        error_msg = str(e)
        # Provide clearer error messages for common issues
        if "dirty" in error_msg.lower():
            print_error(
                "Repository has uncommitted changes",
                "Please commit or stash your changes before running update.",
            )
        elif "subproject" in error_msg.lower():
            print_error(
                "Update failed",
                "Try running `speculate init --overwrite` to reinitialize.",
            )
        else:
            print_error("Update failed", error_msg)
        raise SystemExit(1) from None

    rprint()
    print_success("Docs updated successfully!")
    rprint()

    # Automatically run install to refresh tool configs
    install()


def install(
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    force: bool = False,
) -> None:
    """Generate tool configs for Cursor, Claude Code, and Codex.

    Creates or updates:
      - .speculate/settings.yml (install metadata)
      - CLAUDE.md (for Claude Code) — adds speculate header if missing
      - AGENTS.md (for Codex) — adds speculate header if missing
      - .cursor/rules/ (symlinks for Cursor)
      - .claude/scripts/ensure-gh-cli.sh (GitHub CLI setup hook)
      - .claude/settings.json (Claude Code hook configuration)

    If CLAUDE.md doesn't exist, creates it as a symlink to AGENTS.md.
    If CLAUDE.md already exists as a regular file, updates both files.

    This command is idempotent and can be run multiple times safely.
    It's automatically called by `init` and `update`.

    Supports include/exclude patterns with wildcards:
      - `*` matches any characters within a filename
      - `**` matches any path segments
      - Default: include all (["**/*.md"])

    Use --force to overwrite existing .cursor/rules/ symlinks.

    Examples:
      speculate install
      speculate install --include "general-*.md"
      speculate install --exclude "convex-*.md"
      speculate install --force
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

    claude_md = cwd / "CLAUDE.md"
    agents_md = cwd / "AGENTS.md"

    # Handle CLAUDE.md and AGENTS.md setup
    # If CLAUDE.md doesn't exist, create it as a symlink to AGENTS.md
    if not claude_md.exists() and not claude_md.is_symlink():
        # First ensure AGENTS.md exists with the header
        _ensure_speculate_header(agents_md)
        # Then create CLAUDE.md as a symlink to AGENTS.md
        claude_md.symlink_to("AGENTS.md")
        print_success("Created CLAUDE.md -> AGENTS.md symlink")
    else:
        # CLAUDE.md exists (as file or symlink)
        # _ensure_speculate_header handles symlinks by skipping them
        _ensure_speculate_header(claude_md)
        _ensure_speculate_header(agents_md)

    # .cursor/rules/
    _setup_cursor_rules(cwd, include=include, exclude=exclude, force=force)

    # .claude/ hooks
    _setup_claude_hooks(cwd, force=force)

    rprint()
    print_success("Tool configs installed!")
    rprint()


def status() -> None:
    """Show current template version and sync status.

    Displays:
      - Template version from .speculate/copier-answers.yml
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

    # Check copier answers file (required for update)
    answers_file = cwd / COPIER_ANSWERS_FILE
    if answers_file.exists():
        answers = _load_yaml(answers_file)
        commit = answers.get("_commit", "unknown")
        src = answers.get("_src_path", "unknown")
        print_success(f"Template version: {commit}")
        print_detail(f"Source: {src}")
    else:
        print_error_item(
            f"{COPIER_ANSWERS_FILE} missing (required!)",
            "Run `speculate init` to initialize docs.",
        )
        has_errors = True

    # Check settings file
    settings_file = cwd / SETTINGS_FILE
    if settings_file.exists():
        settings = _load_yaml(settings_file)
        last_update = settings.get("last_update", "unknown")
        cli_version = settings.get("last_cli_version", "unknown")
        print_success(f"Last install: {last_update} (CLI {cli_version})")
    else:
        print_info(f"{SETTINGS_FILE} not found")

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
    settings_dir = project_root / SPECULATE_DIR
    settings_dir.mkdir(parents=True, exist_ok=True)
    settings_file = project_root / SETTINGS_FILE

    # Read existing settings
    settings: dict[str, Any] = _load_yaml(settings_file) if settings_file.exists() else {}

    # Update with current info
    settings["last_update"] = datetime.now(UTC).isoformat()
    try:
        settings["last_cli_version"] = version(PACKAGE_NAME)
    except Exception:
        settings["last_cli_version"] = "unknown"

    # Get docs version from copier answers file if available
    answers_file = project_root / COPIER_ANSWERS_FILE
    if answers_file.exists():
        answers = _load_yaml(answers_file)
        settings["last_docs_version"] = answers.get("_commit", "unknown")

    with atomic_output_file(settings_file) as temp_path:
        Path(temp_path).write_text(yaml.dump(settings, default_flow_style=False))
    print_success(f"Updated {SETTINGS_FILE}")


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

# Regex pattern to match the speculate header block wherever it appears in a file.
# Uses re.MULTILINE so ^ matches start of any line (not just start of file).
# Handles trailing whitespace and blank lines after the header.
SPECULATE_HEADER_PATTERN = re.compile(
    r"^IMPORTANT: You MUST read [^\n]*development\.md[^\n]*\n"
    r"\(This project uses Speculate project structure\.\)[ \t]*\n*",
    re.MULTILINE,
)


def _ensure_speculate_header(path: Path) -> None:
    """Ensure SPECULATE_HEADER is at the top of the file (idempotent).

    If file is a symlink, skip it (will be handled via its target).
    If file exists and already has the marker, do nothing.
    If file exists without marker, prepend the header.
    If file doesn't exist, create with just the header.
    """
    # Skip symlinks - only write to the actual target
    if path.is_symlink():
        target = path.resolve()
        print_info(f"{path.name} is a symlink to {target.name}, skipping")
        return

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
        print_success(f"Removed {path.name} (was empty after header removal)")
    else:
        with atomic_output_file(path) as temp_path:
            Path(temp_path).write_text(new_content)
        print_success(f"Removed speculate header from {path.name}")


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
    force: bool = False,
) -> None:
    """Set up .cursor/rules/ with symlinks to agent-rules directories.

    Collects rules from both docs/general/agent-rules/ and docs/project/agent-rules/,
    with project rules taking precedence over general rules of the same name.

    Note: Cursor requires .mdc extension, so we create symlinks with .mdc
    extension pointing to the source .md files.

    Supports include/exclude patterns for filtering which rules to link.
    Use force=True to overwrite existing symlinks.
    """
    cursor_dir = project_root / ".cursor" / "rules"
    cursor_dir.mkdir(parents=True, exist_ok=True)

    general_rules_dir = project_root / "docs" / "general" / "agent-rules"
    project_rules_dir = project_root / "docs" / "project" / "agent-rules"

    # Collect rules from both sources, project takes precedence
    # Maps stem -> (source_path, relative_dir_for_symlink)
    rules: dict[str, tuple[Path, str]] = {}

    if general_rules_dir.exists():
        for rule_file in general_rules_dir.glob("*.md"):
            rules[rule_file.stem] = (rule_file, "docs/general/agent-rules")
    else:
        print_warning("docs/general/agent-rules/ not found")

    if project_rules_dir.exists():
        for rule_file in project_rules_dir.glob("*.md"):
            # Project rules override general rules of same name
            rules[rule_file.stem] = (rule_file, "docs/project/agent-rules")

    if not rules:
        print_warning("No agent-rules found, skipping Cursor setup")
        return

    linked_count = 0
    skipped_by_pattern = 0
    skipped_existing = 0

    for stem in sorted(rules.keys()):
        rule_path, relative_dir = rules[stem]

        # Check include/exclude patterns
        if not _matches_patterns(rule_path.name, include, exclude):
            skipped_by_pattern += 1
            continue

        # Cursor requires .mdc extension
        link_name = stem + ".mdc"
        link_path = cursor_dir / link_name

        if link_path.exists() or link_path.is_symlink():
            if not force:
                skipped_existing += 1
                continue
            link_path.unlink()

        # Create relative symlink
        relative_target = Path("..") / ".." / relative_dir / rule_path.name
        link_path.symlink_to(relative_target)
        linked_count += 1

    # Build informative message
    msg_parts: list[str] = []
    if linked_count:
        msg_parts.append(f"linked {linked_count}")
    if skipped_existing:
        msg_parts.append(f"skipped {skipped_existing} existing")
    if skipped_by_pattern:
        msg_parts.append(f"skipped {skipped_by_pattern} by pattern")

    if msg_parts:
        msg = ".cursor/rules/: " + ", ".join(msg_parts)
        print_success(msg)
    else:
        print_info(".cursor/rules/: no changes")


def _remove_cursor_rules(project_root: Path) -> None:
    """Remove .cursor/rules/*.mdc symlinks that point to speculate docs.

    Only removes symlinks, not regular files. Also removes broken symlinks.
    Handles symlinks to both docs/general/agent-rules/ and docs/project/agent-rules/.
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
                # Remove if it points to docs/general/agent-rules/ or docs/project/agent-rules/ or is broken
                target_str = str(target)
                if (
                    "docs/general/agent-rules" in target_str
                    or "docs/project/agent-rules" in target_str
                    or not target.exists()
                ):
                    link_path.unlink()
                    removed_count += 1
            except OSError:
                # Broken symlink, remove it
                link_path.unlink()
                removed_count += 1

    if removed_count > 0:
        print_success(f"Removed {removed_count} symlinks from .cursor/rules/")


# Claude Code hooks - loaded from resources/claude-hooks/
CLAUDE_HOOKS_RESOURCE = "speculate.cli.resources.claude-hooks"


def _get_claude_hooks_resource() -> Any:
    """Get the claude-hooks resource directory."""
    return files(CLAUDE_HOOKS_RESOURCE)


def _setup_claude_hooks(project_root: Path, force: bool = False) -> None:
    """Set up .claude/ directory with hooks from resources.

    Copies scripts from resources/claude-hooks/scripts/ to .claude/scripts/
    and merges hook definitions from resources/claude-hooks/hooks.json into
    .claude/settings.json.

    Handles merging with existing settings.json (preserves user hooks).
    Never touches .claude/settings.local.json (user's local overrides).
    """
    resource_dir = _get_claude_hooks_resource()
    claude_dir = project_root / ".claude"
    scripts_dir = claude_dir / "scripts"
    settings_file = claude_dir / "settings.json"

    # Create directories
    scripts_dir.mkdir(parents=True, exist_ok=True)

    # Copy all scripts from resources
    scripts_resource = resource_dir.joinpath("scripts")
    for script_file in scripts_resource.iterdir():
        if script_file.name.endswith(".sh"):
            dest_file = scripts_dir / script_file.name
            script_content = script_file.read_text()
            action = _copy_script_file(dest_file, script_content, force)
            if action:
                print_success(f".claude/scripts/{script_file.name}: {action}")

    # Merge hooks.json into settings.json
    hooks_resource = resource_dir.joinpath("hooks.json")
    hooks_config = json.loads(hooks_resource.read_text())
    action = _merge_claude_settings(settings_file, hooks_config)
    if action:
        print_success(f".claude/settings.json: {action}")


def _copy_script_file(dest_file: Path, content: str, force: bool) -> str | None:
    """Copy a script file to destination. Returns action description or None if no change."""
    if dest_file.exists():
        existing_content = dest_file.read_text()
        if existing_content == content:
            return None  # Already up to date
        if not force:
            print_warning(
                f".claude/scripts/{dest_file.name} modified, skipping (use --force to overwrite)"
            )
            return None
        # Force overwrite
        with atomic_output_file(dest_file) as temp_path:
            Path(temp_path).write_text(content)
        dest_file.chmod(0o755)
        return "updated (forced)"

    # Create new script
    with atomic_output_file(dest_file) as temp_path:
        Path(temp_path).write_text(content)
    dest_file.chmod(0o755)
    return "created"


def _merge_claude_settings(settings_file: Path, hooks_to_add: dict[str, list[Any]]) -> str | None:
    """Merge hook definitions into settings.json.

    Returns action description or None if no change needed.
    """
    settings: dict[str, Any]
    if settings_file.exists():
        try:
            parsed = json.loads(settings_file.read_text())
            settings = cast(dict[str, Any], parsed) if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            print_warning(".claude/settings.json has invalid JSON, skipping")
            return None
    else:
        settings = {}

    hooks: dict[str, list[Any]] = settings.setdefault("hooks", {})
    changes_made = False

    # Merge each hook type from hooks_to_add
    # JSON parsing produces dynamic types, so we use cast for type narrowing
    for hook_type, new_entries in hooks_to_add.items():
        existing_entries: list[Any] = hooks.get(hook_type, [])

        for new_entry in new_entries:
            # Check if this entry already exists (by matching command in hooks)
            already_exists = False
            new_entry_dict = cast(dict[str, Any], new_entry) if isinstance(new_entry, dict) else {}
            new_hooks_list: list[Any] = new_entry_dict.get("hooks", [])
            new_commands: set[str] = {
                cast(dict[str, Any], h).get("command", "")
                for h in new_hooks_list
                if isinstance(h, dict)
            }

            for existing_entry in existing_entries:
                if isinstance(existing_entry, dict):
                    existing_entry_dict = cast(dict[str, Any], existing_entry)
                    existing_hooks_list: list[Any] = existing_entry_dict.get("hooks", [])
                    existing_commands: set[str] = {
                        cast(dict[str, Any], h).get("command", "")
                        for h in existing_hooks_list
                        if isinstance(h, dict)
                    }
                    if new_commands & existing_commands:
                        already_exists = True
                        break

            if not already_exists:
                existing_entries.append(new_entry)
                changes_made = True

        hooks[hook_type] = existing_entries

    if not changes_made:
        return None

    was_new = not settings_file.exists()
    with atomic_output_file(settings_file) as temp_path:
        Path(temp_path).write_text(json.dumps(settings, indent=2) + "\n")

    return "created" if was_new else "updated hooks"


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

    print_header("Uninstalling Speculate tool configs...", cwd)

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

    settings_file = cwd / SETTINGS_FILE
    if settings_file.exists():
        changes.append(f"Remove {SETTINGS_FILE}")

    if not changes:
        print_info("Nothing to uninstall")
        return

    rprint("[bold]Will perform:[/bold]")
    for change in changes:
        print_detail(change)
    rprint()

    if not force:
        response = input("Proceed? [y/N] ").strip().lower()
        if response != "y":
            print_cancelled()
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
        print_success(f"Removed {SETTINGS_FILE}")

    rprint()
    print_success("Uninstall complete!")
    print_info("Note: docs/ directory preserved. Remove manually if desired.")
    rprint()
