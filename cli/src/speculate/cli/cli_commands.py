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
from pathlib import Path
from textwrap import dedent
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

# Claude Code plugin configuration
CLAUDE_PLUGIN_NAME = "speculate"
CLAUDE_PLUGIN_DIR = f".claude/plugins/{CLAUDE_PLUGIN_NAME}"
CLAUDE_PLUGIN_DESCRIPTION = (
    "Spec-driven development workflows: planning, implementation, commits, PRs, and code review"
)
CLAUDE_PLUGIN_REPOSITORY = "https://github.com/jlevy/speculate"
CLAUDE_PLUGIN_HOMEPAGE = "https://github.com/jlevy/speculate"


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
    global_install: bool = False,
) -> None:
    """Generate tool configs for Cursor, Claude Code, and Codex.

    Creates or updates:
      - .speculate/settings.yml (install metadata)
      - CLAUDE.md (for Claude Code) — adds speculate header if missing
      - AGENTS.md (for Codex) — adds speculate header if missing
      - .cursor/rules/ (symlinks for Cursor)
      - .claude/plugins/speculate/ (Claude Code plugin with commands and skill)

    If CLAUDE.md doesn't exist, creates it as a symlink to AGENTS.md.
    If CLAUDE.md already exists as a regular file, updates both files.

    This command is idempotent and can be run multiple times safely.
    It's automatically called by `init` and `update`.

    Supports include/exclude patterns with wildcards:
      - `*` matches any characters within a filename
      - `**` matches any path segments
      - Default: include all (["**/*.md"])

    Use --force to overwrite existing symlinks and regenerate generated files.
    Use --global to install the plugin to ~/.claude/plugins/ for personal use.

    Examples:
      speculate install
      speculate install --include "general-*.md"
      speculate install --exclude "convex-*.md"
      speculate install --force
      speculate install --global  # Personal installation to ~/.claude/plugins/
    """
    # Handle global installation separately
    if global_install:
        print_header("Installing Speculate plugin globally...", Path.home())
        _setup_global_claude_plugin(force=force)
        rprint()
        print_success("Global plugin installed!")
        print_info("Note: Run `speculate install` in a project to add commands.")
        rprint()
        return
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

    # .claude/plugins/speculate/
    _setup_claude_plugin(cwd, include=include, exclude=exclude, force=force)

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

    # Check Claude Code plugin (project-level)
    claude_plugin = cwd / CLAUDE_PLUGIN_DIR
    if claude_plugin.exists():
        commands_dir = claude_plugin / "commands"
        if commands_dir.exists():
            command_count = len(list(commands_dir.glob("*.md")))
            print_success(f"{CLAUDE_PLUGIN_DIR}/ exists ({command_count} commands)")
        else:
            print_warning(f"{CLAUDE_PLUGIN_DIR}/ exists but has no commands")
    else:
        print_info(f"{CLAUDE_PLUGIN_DIR}/ not configured")

    # Check global Claude Code plugin
    home = Path.home()
    global_plugin = home / ".claude" / "plugins" / CLAUDE_PLUGIN_NAME
    if global_plugin.exists():
        print_success(f"~/.claude/plugins/{CLAUDE_PLUGIN_NAME}/ exists (global)")
    else:
        print_info(f"~/.claude/plugins/{CLAUDE_PLUGIN_NAME}/ not configured (global)")

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


def _get_plugin_version() -> str:
    """Get the plugin version from the CLI package version."""
    try:
        return version(PACKAGE_NAME)
    except Exception:
        return "0.0.0"


def _generate_plugin_json() -> str:
    """Generate plugin.json content for the Speculate Claude Code plugin."""
    plugin_data = {
        "name": CLAUDE_PLUGIN_NAME,
        "version": _get_plugin_version(),
        "description": CLAUDE_PLUGIN_DESCRIPTION,
        "author": {"name": "Speculate"},
        "repository": CLAUDE_PLUGIN_REPOSITORY,
        "homepage": CLAUDE_PLUGIN_HOMEPAGE,
    }
    return json.dumps(plugin_data, indent=2) + "\n"


def _generate_plugin_readme(command_count: int) -> str:
    """Generate README.md content for the Speculate plugin."""
    return dedent(f"""
        # Speculate Plugin for Claude Code

        This plugin provides spec-driven development workflows for Claude Code.

        ## What's Included

        - **{command_count} commands**: Type `/speculate:` to see available commands
        - **1 skill**: `speculate-workflow` for automatic workflow detection

        ## Usage

        Commands are invoked as `/speculate:command-name`. For example:
        - `/speculate:new-plan-spec` - Create a feature plan
        - `/speculate:implement-beads` - Implement work items
        - `/speculate:commit-code` - Commit with pre-commit checks

        The routing skill automatically suggests relevant commands based on your task.

        ## Common Workflow Chains

        **Full Feature Flow:**
        1. `/speculate:new-plan-spec`
        2. `/speculate:new-implementation-beads-from-spec`
        3. `/speculate:implement-beads`
        4. `/speculate:create-or-update-pr-with-validation-plan`

        **Commit Flow:**
        1. `/speculate:precommit-process`
        2. `/speculate:commit-code`

        ## Source

        Commands are symlinked from `docs/general/agent-shortcuts/`. Edit the source
        files to customize behavior.

        ## More Information

        - Repository: {CLAUDE_PLUGIN_REPOSITORY}
        - CLI: `pip install {PACKAGE_NAME}`
        """).strip() + "\n"


def _generate_hooks_json(include_session_start: bool = True) -> str:
    """Generate hooks.json for lifecycle automation."""
    hooks_data: dict[str, Any] = {"hooks": {}}

    if include_session_start:
        hooks_data["hooks"]["SessionStart"] = [{
            "matcher": "*",
            "hooks": [{
                "type": "command",
                "command": "echo 'Speculate workflows available. Type /speculate: to see commands.'"
            }]
        }]

    return json.dumps(hooks_data, indent=2) + "\n"


# Maps shortcut stems to human-readable descriptions for the routing skill.
SHORTCUT_TRIGGER_DESCRIPTIONS: dict[str, str] = {
    "new-plan-spec": "Creating a new feature plan",
    "new-implementation-spec": "Creating an implementation spec",
    "new-implementation-beads-from-spec": "Creating implementation beads from a spec",
    "new-validation-spec": "Creating a validation/test spec",
    "refine-spec": "Refining or clarifying an existing spec",
    "update-spec": "Updating a spec with new information",
    "update-specs-status": "Updating specs progress and beads",
    "implement-beads": "Implementing beads",
    "implement-spec": "Implementing a spec",
    "coding-spike": "Exploratory coding / prototype / spike",
    "precommit-process": "Running pre-commit checks",
    "commit-code": "Committing code",
    "create-or-update-validation-plan": "Creating a validation plan",
    "create-or-update-pr-with-validation-plan": "Creating a PR with validation",
    "create-pr-simple": "Creating a PR (simple)",
    "review-all-code-specs-docs-convex": "Reviewing code, specs, docs",
    "review-pr": "Reviewing a PR",
    "review-pr-and-fix-with-beads": "Reviewing and fixing a PR with beads",
    "new-research-brief": "Research or technical investigation",
    "new-architecture-doc": "Creating architecture documentation",
    "revise-architecture-doc": "Updating/revising architecture docs",
    "cleanup-all": "Code cleanup or refactoring",
    "cleanup-remove-trivial-tests": "Removing trivial tests",
    "cleanup-update-docstrings": "Updating docstrings",
    "merge-upstream": "Merging from upstream",
    "setup-github-cli": "Setting up GitHub CLI",
    "setup-beads": "Setting up beads",
}


def _generate_skill_md(shortcut_names: list[str]) -> str:
    """
    Generate SKILL.md content for the routing skill.

    Creates a skill that Claude Code will automatically invoke based on
    semantic matching, directing it to use the appropriate /speculate:* command.
    """
    # Build trigger table rows for available shortcuts
    trigger_rows: list[str] = []
    for name in sorted(shortcut_names):
        stem = name.replace(".md", "")
        description = SHORTCUT_TRIGGER_DESCRIPTIONS.get(stem, f"Using {stem}")
        trigger_rows.append(f"| {description} | /speculate:{stem} |")

    trigger_table = "\n".join(trigger_rows)

    return dedent(f"""
        ---
        name: speculate-workflow
        description: Spec-driven development workflow automation. Activates for feature planning,
          implementation specs, code commits, PR creation, code review, research briefs,
          architecture docs, cleanup tasks, and any development workflow that benefits from
          structured methodology.
        ---

        # Speculate Workflow Router

        Before responding to ANY coding or development request, you MUST check if a
        Speculate command applies. If a command applies, you MUST use it.

        ## Trigger Table

        | If user request involves... | Use command |
        |----------------------------|-------------|
        {trigger_table}

        ## Common Workflow Chains

        ### Full Feature Flow
        1. /speculate:new-plan-spec
        2. /speculate:new-implementation-beads-from-spec
        3. /speculate:implement-beads
        4. /speculate:create-or-update-pr-with-validation-plan

        ### Commit Flow
        1. /speculate:precommit-process
        2. /speculate:commit-code

        ### PR Flow (Prerequisites)
        Before creating a PR:
        1. Ensure GitHub CLI is configured: /speculate:setup-github-cli
        2. Run pre-commit checks: /speculate:precommit-process
        3. Create PR: /speculate:create-or-update-pr-with-validation-plan

        ## This is NOT Optional

        If a command exists for your task, you MUST use it.
        Do not rationalize skipping it:
        - "This is simple" → WRONG. Use the command.
        - "I know how to do this" → WRONG. The command has steps you'll forget.
        - "The user didn't ask" → WRONG. Commands are mandatory when applicable.

        ## Session Close Protocol

        Before saying "done" or "complete", ensure:
        1. All code changes are committed
        2. Changes are pushed to remote
        3. PR is created if on a feature branch

        Work is not done until pushed.

        ## Usage

        When a matching trigger is detected:
        1. Announce: "Using /speculate:[command-name]"
        2. Invoke the command
        3. Follow the command's instructions exactly

        ## Token Budget

        This skill adds approximately 400-500 tokens to context when activated.
        The trigger table and workflow chains are designed to be concise while
        providing clear routing guidance.

        To minimize token usage:
        - The skill only activates when semantic matching triggers it
        - Detailed command instructions are in the command files (loaded on demand)
        - Keep your prompts focused on the task at hand
        """).strip() + "\n"


def _setup_claude_plugin(
    project_root: Path,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    force: bool = False,
    with_hooks: bool = True,
) -> None:
    """
    Set up .claude/plugins/speculate/ with symlinks to shortcuts.

    Collects shortcuts from:
      - docs/general/agent-shortcuts/shortcut:*.md
      - docs/general/agent-setup/shortcut:*.md
      - docs/project/agent-shortcuts/shortcut:*.md (if exists, takes precedence)

    Creates:
      - .claude/plugins/speculate/.claude-plugin/plugin.json
      - .claude/plugins/speculate/README.md
      - .claude/plugins/speculate/commands/*.md (symlinks)
      - .claude/plugins/speculate/skills/speculate-workflow/SKILL.md
      - .claude/plugins/speculate/hooks/hooks.json (if with_hooks=True)
      - .claude/plugins/speculate/reference/ (symlinks to agent-rules)

    Symlinks strip the 'shortcut:' prefix for clean command names.
    """
    plugin_dir = project_root / CLAUDE_PLUGIN_DIR
    commands_dir = plugin_dir / "commands"
    skills_dir = plugin_dir / "skills" / "speculate-workflow"
    manifest_dir = plugin_dir / ".claude-plugin"
    hooks_dir = plugin_dir / "hooks"
    reference_dir = plugin_dir / "reference"

    # Collect shortcuts from all sources
    # Maps: clean_name -> (source_path, relative_dir_for_symlink)
    shortcuts: dict[str, tuple[Path, str]] = {}

    # General shortcuts
    general_shortcuts_dir = project_root / "docs" / "general" / "agent-shortcuts"
    if general_shortcuts_dir.exists():
        for shortcut_file in general_shortcuts_dir.glob("shortcut:*.md"):
            clean_name = shortcut_file.name.replace("shortcut:", "")
            shortcuts[clean_name] = (shortcut_file, "docs/general/agent-shortcuts")

    # Agent-setup shortcuts
    agent_setup_dir = project_root / "docs" / "general" / "agent-setup"
    if agent_setup_dir.exists():
        for shortcut_file in agent_setup_dir.glob("shortcut:*.md"):
            clean_name = shortcut_file.name.replace("shortcut:", "")
            shortcuts[clean_name] = (shortcut_file, "docs/general/agent-setup")

    # Project shortcuts (override general)
    project_shortcuts_dir = project_root / "docs" / "project" / "agent-shortcuts"
    if project_shortcuts_dir.exists():
        for shortcut_file in project_shortcuts_dir.glob("shortcut:*.md"):
            clean_name = shortcut_file.name.replace("shortcut:", "")
            shortcuts[clean_name] = (shortcut_file, "docs/project/agent-shortcuts")

    if not shortcuts:
        print_warning("No shortcuts found, skipping Claude Code plugin setup")
        return

    # Create directory structure
    commands_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    reference_dir.mkdir(parents=True, exist_ok=True)
    if with_hooks:
        hooks_dir.mkdir(parents=True, exist_ok=True)

    # Generate plugin.json
    plugin_json = _generate_plugin_json()
    plugin_json_path = manifest_dir / "plugin.json"
    if not plugin_json_path.exists() or force:
        with atomic_output_file(plugin_json_path) as temp_path:
            Path(temp_path).write_text(plugin_json)
        print_success(f"Generated {CLAUDE_PLUGIN_DIR}/.claude-plugin/plugin.json")

    # Generate README.md
    readme_path = plugin_dir / "README.md"
    if not readme_path.exists() or force:
        readme_content = _generate_plugin_readme(len(shortcuts))
        with atomic_output_file(readme_path) as temp_path:
            Path(temp_path).write_text(readme_content)
        print_success(f"Generated {CLAUDE_PLUGIN_DIR}/README.md")

    # Generate hooks.json (optional)
    if with_hooks:
        hooks_json_path = hooks_dir / "hooks.json"
        if not hooks_json_path.exists() or force:
            hooks_content = _generate_hooks_json()
            with atomic_output_file(hooks_json_path) as temp_path:
                Path(temp_path).write_text(hooks_content)
            print_success(f"Generated {CLAUDE_PLUGIN_DIR}/hooks/hooks.json")

    # Create symlinks for each shortcut
    linked_count = 0
    skipped_by_pattern = 0
    skipped_existing = 0

    for clean_name in sorted(shortcuts.keys()):
        source_path, relative_dir = shortcuts[clean_name]

        # Check include/exclude patterns (use original filename with shortcut: prefix)
        if not _matches_patterns(source_path.name, include, exclude):
            skipped_by_pattern += 1
            continue

        link_path = commands_dir / clean_name

        if link_path.exists() or link_path.is_symlink():
            if not force:
                skipped_existing += 1
                continue
            link_path.unlink()

        # Calculate relative path: commands/ is 4 levels deep from project root
        # .claude/plugins/speculate/commands/file.md -> docs/.../shortcut:file.md
        relative_target = (
            Path("..") / ".." / ".." / ".." / relative_dir / source_path.name
        )
        link_path.symlink_to(relative_target)
        linked_count += 1

    # Generate SKILL.md for automatic triggering
    skill_md = _generate_skill_md(list(shortcuts.keys()))
    skill_md_path = skills_dir / "SKILL.md"
    if not skill_md_path.exists() or force:
        with atomic_output_file(skill_md_path) as temp_path:
            Path(temp_path).write_text(skill_md)
        print_success(f"Generated {CLAUDE_PLUGIN_DIR}/skills/speculate-workflow/SKILL.md")

    # Create reference symlinks to agent-rules
    ref_linked = 0
    general_rules_dir = project_root / "docs" / "general" / "agent-rules"
    project_rules_dir = project_root / "docs" / "project" / "agent-rules"

    # Collect rules from both sources, project takes precedence
    rules: dict[str, tuple[Path, str]] = {}
    if general_rules_dir.exists():
        for rule_file in general_rules_dir.glob("*.md"):
            rules[rule_file.stem] = (rule_file, "docs/general/agent-rules")
    if project_rules_dir.exists():
        for rule_file in project_rules_dir.glob("*.md"):
            rules[rule_file.stem] = (rule_file, "docs/project/agent-rules")

    for stem in sorted(rules.keys()):
        rule_path, relative_dir = rules[stem]
        link_path = reference_dir / rule_path.name

        if link_path.exists() or link_path.is_symlink():
            if not force:
                continue
            link_path.unlink()

        # reference/ is 4 levels deep: .claude/plugins/speculate/reference/
        relative_target = Path("..") / ".." / ".." / ".." / relative_dir / rule_path.name
        link_path.symlink_to(relative_target)
        ref_linked += 1

    if ref_linked > 0:
        print_success(f"Linked {ref_linked} agent-rules to {CLAUDE_PLUGIN_DIR}/reference/")

    # Status message
    msg_parts: list[str] = []
    if linked_count:
        msg_parts.append(f"linked {linked_count} commands")
    if skipped_existing:
        msg_parts.append(f"skipped {skipped_existing} existing")
    if skipped_by_pattern:
        msg_parts.append(f"skipped {skipped_by_pattern} by pattern")

    if msg_parts:
        msg = f"{CLAUDE_PLUGIN_DIR}/: " + ", ".join(msg_parts)
        print_success(msg)
    else:
        print_info(f"{CLAUDE_PLUGIN_DIR}/: no changes")


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


def _setup_global_claude_plugin(force: bool = False) -> None:
    """
    Install Speculate plugin globally to ~/.claude/plugins/speculate/.

    This creates a personal installation that provides the base plugin
    without project-specific commands. Useful for having the plugin
    available across all Claude Code sessions.

    Creates:
      - ~/.claude/plugins/speculate/.claude-plugin/plugin.json
      - ~/.claude/plugins/speculate/README.md
      - ~/.claude/plugins/speculate/skills/speculate-workflow/SKILL.md
      - ~/.claude/plugins/speculate/hooks/hooks.json

    Note: Commands are not installed globally since they require project
    context. Use `speculate install` in a project to add commands.
    """
    home = Path.home()
    plugin_dir = home / ".claude" / "plugins" / CLAUDE_PLUGIN_NAME
    skills_dir = plugin_dir / "skills" / "speculate-workflow"
    manifest_dir = plugin_dir / ".claude-plugin"
    hooks_dir = plugin_dir / "hooks"

    # Create directory structure
    skills_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    hooks_dir.mkdir(parents=True, exist_ok=True)

    # Generate plugin.json
    plugin_json = _generate_plugin_json()
    plugin_json_path = manifest_dir / "plugin.json"
    if not plugin_json_path.exists() or force:
        with atomic_output_file(plugin_json_path) as temp_path:
            Path(temp_path).write_text(plugin_json)
        print_success("Generated ~/.claude/plugins/speculate/.claude-plugin/plugin.json")

    # Generate README.md (with 0 commands since global install has no commands)
    readme_path = plugin_dir / "README.md"
    if not readme_path.exists() or force:
        readme_content = _generate_plugin_readme(0).replace(
            "- **0 commands**: Type `/speculate:` to see available commands",
            "- **Commands**: Run `speculate install` in a project to add commands"
        )
        with atomic_output_file(readme_path) as temp_path:
            Path(temp_path).write_text(readme_content)
        print_success("Generated ~/.claude/plugins/speculate/README.md")

    # Generate hooks.json
    hooks_json_path = hooks_dir / "hooks.json"
    if not hooks_json_path.exists() or force:
        hooks_content = _generate_hooks_json()
        with atomic_output_file(hooks_json_path) as temp_path:
            Path(temp_path).write_text(hooks_content)
        print_success("Generated ~/.claude/plugins/speculate/hooks/hooks.json")

    # Generate SKILL.md (with no specific commands, just guidance)
    skill_md_path = skills_dir / "SKILL.md"
    if not skill_md_path.exists() or force:
        skill_content = dedent("""
            ---
            name: speculate-workflow
            description: Spec-driven development workflow automation. Activates for feature planning,
              implementation specs, code commits, PR creation, code review, research briefs,
              architecture docs, cleanup tasks, and any development workflow that benefits from
              structured methodology.
            ---

            # Speculate Workflow Router (Global)

            This is the global Speculate plugin installation. To get project-specific
            commands, run `speculate install` in your project directory.

            ## Available Workflows

            When working in a project with Speculate installed, these workflows are available:

            - **Feature Planning**: Create spec-driven feature plans
            - **Implementation**: Create beads and implement systematically
            - **Code Review**: Pre-commit checks and PR creation
            - **Research**: Technical investigation and documentation

            ## Setup

            To enable commands in the current project:

            ```bash
            speculate install
            ```

            This will add `/speculate:*` commands to your project.
            """).strip() + "\n"
        with atomic_output_file(skill_md_path) as temp_path:
            Path(temp_path).write_text(skill_content)
        print_success("Generated ~/.claude/plugins/speculate/skills/speculate-workflow/SKILL.md")


def _remove_global_claude_plugin() -> None:
    """
    Remove ~/.claude/plugins/speculate/ directory.

    Only removes the speculate plugin, not other plugins or .claude/ content.
    """
    home = Path.home()
    plugin_dir = home / ".claude" / "plugins" / CLAUDE_PLUGIN_NAME

    if not plugin_dir.exists():
        return

    shutil.rmtree(plugin_dir)
    print_success("Removed ~/.claude/plugins/speculate/")

    # Clean up empty parent directories
    plugins_dir = plugin_dir.parent
    if plugins_dir.exists() and not any(plugins_dir.iterdir()):
        plugins_dir.rmdir()

    claude_dir = plugins_dir.parent
    if claude_dir.exists() and not any(claude_dir.iterdir()):
        claude_dir.rmdir()


def _remove_claude_plugin(project_root: Path) -> None:
    """
    Remove .claude/plugins/speculate/ directory.

    Only removes the speculate plugin, not other plugins or .claude/ content.
    Cleans up empty parent directories if possible.
    """
    plugin_dir = project_root / CLAUDE_PLUGIN_DIR
    if not plugin_dir.exists():
        return

    # Remove the entire plugin directory
    shutil.rmtree(plugin_dir)
    print_success(f"Removed {CLAUDE_PLUGIN_DIR}/")

    # Clean up empty parent directories
    plugins_dir = plugin_dir.parent  # .claude/plugins/
    if plugins_dir.exists() and not any(plugins_dir.iterdir()):
        plugins_dir.rmdir()

    claude_dir = plugins_dir.parent  # .claude/
    if claude_dir.exists() and not any(claude_dir.iterdir()):
        claude_dir.rmdir()


def uninstall(force: bool = False, global_install: bool = False) -> None:
    """Remove tool configs installed by speculate.

    Removes:
      - Speculate header from CLAUDE.md (preserves other content)
      - Speculate header from AGENTS.md (preserves other content)
      - .cursor/rules/*.mdc symlinks that point to speculate docs
      - .claude/plugins/speculate/ (entire plugin directory)
      - .speculate/settings.yml

    Does NOT remove:
      - docs/ directory (remove manually if desired)
      - .speculate/copier-answers.yml (needed for `speculate update`)

    If CLAUDE.md or AGENTS.md becomes empty after header removal, the file
    is deleted entirely.

    Use --global to uninstall from ~/.claude/plugins/ instead of project.

    Examples:
      speculate uninstall           # Uninstall with confirmation
      speculate uninstall --force   # Uninstall without confirmation
      speculate uninstall --global  # Uninstall global plugin
    """
    # Handle global uninstall
    if global_install:
        home = Path.home()
        global_plugin = home / ".claude" / "plugins" / CLAUDE_PLUGIN_NAME

        if not global_plugin.exists():
            print_info("No global plugin installed")
            return

        print_header("Uninstalling global Speculate plugin...", home)
        rprint("[bold]Will remove:[/bold]")
        print_detail(f"~/.claude/plugins/{CLAUDE_PLUGIN_NAME}/")
        rprint()

        if not force:
            response = input("Proceed? [y/N] ").strip().lower()
            if response != "y":
                print_cancelled()
                raise SystemExit(0)

        rprint()
        _remove_global_claude_plugin()
        rprint()
        print_success("Global plugin uninstalled!")
        rprint()
        return
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

    claude_plugin = cwd / CLAUDE_PLUGIN_DIR
    if claude_plugin.exists():
        commands_dir = claude_plugin / "commands"
        command_count = len(list(commands_dir.glob("*.md"))) if commands_dir.exists() else 0
        changes.append(f"Remove {CLAUDE_PLUGIN_DIR}/ ({command_count} commands)")

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

    # Remove .claude/plugins/speculate/
    _remove_claude_plugin(cwd)

    # Remove .speculate/settings.yml
    if settings_file.exists():
        settings_file.unlink()
        print_success(f"Removed {SETTINGS_FILE}")

    rprint()
    print_success("Uninstall complete!")
    print_info("Note: docs/ directory preserved. Remove manually if desired.")
    rprint()
