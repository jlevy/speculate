# Plan Spec: Claude Code Plugin Support

## Purpose

This is a technical design doc for adding Claude Code plugin support to the Speculate CLI.
The goal is to make Speculate shortcuts and rules discoverable and usable in Claude Code
while maintaining compatibility with other coding agents (Cursor, Codex, etc.).

## Background

### Research Reference

For comprehensive background on coding agent extension mechanisms, see:
[research-coding-agent-skills-commands-extensions.md](../../../../docs/general/research/current/research-coding-agent-skills-commands-extensions.md)

Key findings relevant to this implementation:

| Mechanism | Invocation | Use in Speculate |
|-----------|------------|------------------|
| **Skills** | Automatic (semantic matching) | Routing skill for auto-triggering shortcuts |
| **Commands** | Explicit (`/command-name`) | Shortcuts become `/speculate:*` commands |
| **Plugins** | Distribution bundle | Bundle commands + routing skill together |

### Current State

The Speculate CLI currently supports:
- **Cursor**: `.cursor/rules/` symlinks to `docs/general/agent-rules/*.md` (with `.mdc` extension)
- **Claude Code/Codex**: `CLAUDE.md` and `AGENTS.md` header files pointing to docs
- **All agents**: Direct `@` references to docs in shortcuts and rules

The repository contains:
- **25 agent shortcuts** in `docs/general/agent-shortcuts/` (named `shortcut:*.md`)
- **13 agent rules** in `docs/general/agent-rules/`
- **4 agent guidelines** in `docs/general/agent-guidelines/`
- **2 agent setup guides** in `docs/general/agent-setup/`

### The Problem

Currently, Claude Code users must:
1. Manually reference shortcuts via `@docs/general/agent-shortcuts/shortcut:new-plan-spec.md`
2. Have no auto-discovery of available shortcuts
3. Have no automatic triggering based on task context

Cursor users get symlinked rules but not shortcuts. There's no first-class integration
with Claude Code's plugin/skill/command system.

### Reference: Current CLI Symlink Pattern

The CLI already implements symlinks for Cursor in `_setup_cursor_rules()`:

```python
def _setup_cursor_rules(project_root: Path, ...):
    cursor_dir = project_root / ".cursor" / "rules"
    cursor_dir.mkdir(parents=True, exist_ok=True)

    for rule_file in rules_dir.glob("*.md"):
        link_name = rule_file.stem + ".mdc"
        link_path = cursor_dir / link_name
        relative_target = Path("..") / ".." / "docs" / "general" / "agent-rules" / rule_file.name
        link_path.symlink_to(relative_target)
```

This pattern will be reused for Claude Code plugin setup.

## Summary of Task

Extend the Speculate CLI to create a Claude Code plugin during `speculate install` that:

1. **Creates a plugin structure** at `.claude/plugins/speculate/`
2. **Symlinks all shortcuts** as commands (invoking as `/speculate:new-plan-spec`, etc.)
3. **Generates a routing skill** that implements automatic shortcut triggering
4. **Generates `plugin.json`** manifest

### Key Design Decisions

| # | Decision | Resolution |
|---|----------|------------|
| 1 | Plugin name | `speculate` (commands invoke as `/speculate:command-name`) |
| 2 | Source of truth | Shortcuts remain in `docs/general/agent-shortcuts/` |
| 3 | Command linking | Symlinks from `.claude/plugins/speculate/commands/` to docs |
| 4 | Symlink naming | Strip `shortcut:` prefix (e.g., `new-plan-spec.md` → `shortcut:new-plan-spec.md`) |
| 5 | Auto-triggering | Implemented via a skill with trigger table in instructions |
| 6 | Skill generation | Generated `SKILL.md` based on `automatic-shortcut-triggers.md` |
| 7 | Uninstall | Remove `.claude/plugins/speculate/` directory |
| 8 | Include/exclude | Support patterns for filtering which shortcuts become commands |

### Command Naming

The symlink structure ensures clean command names:

```
.claude/plugins/speculate/commands/
├── new-plan-spec.md          → ../../../docs/general/agent-shortcuts/shortcut:new-plan-spec.md
├── implement-spec.md         → ../../../docs/general/agent-shortcuts/shortcut:implement-spec.md
├── commit-code.md            → ../../../docs/general/agent-shortcuts/shortcut:commit-code.md
└── ...
```

Resulting invocations:
- `/speculate:new-plan-spec`
- `/speculate:implement-spec`
- `/speculate:commit-code`

The colon in source filenames (`shortcut:*.md`) is irrelevant - only the symlink name matters.

## Backward Compatibility

| Area | Impact | Handling |
|------|--------|----------|
| Existing `.claude/` directories | May exist with user content | Only create/modify `.claude/plugins/speculate/` |
| CLAUDE.md header | Already exists | No change needed |
| Cursor rules | Already exist | No change needed |
| Shortcut file format | Already works | No change needed |

## Stage 1: Planning Stage

### Minimum Viable Features

**Must Have:**

- [x] Create `.claude/plugins/speculate/` directory structure
- [x] Generate `.claude/plugins/speculate/.claude-plugin/plugin.json`
- [x] Symlink all shortcuts from `docs/general/agent-shortcuts/shortcut:*.md` to commands
- [x] Generate routing skill at `.claude/plugins/speculate/skills/speculate-workflow/SKILL.md`
- [x] Update `speculate install` to call new `_setup_claude_plugin()` function
- [x] Update `speculate uninstall` to remove `.claude/plugins/speculate/`
- [x] Update `speculate status` to show Claude Code plugin status
- [x] Support `--include` and `--exclude` patterns for shortcuts

**Nice to Have (v2):**

- [x] Symlink agent-rules as well (for context in skill instructions) - Done in v2
- [x] Support for agent-setup shortcuts (DONE - included in v1 implementation)
- [x] Personal installation to `~/.claude/plugins/` - Done in v2 with `--global` flag

**Not In Scope:**

- Plugin marketplace distribution (manual installation only)
- MCP server integration
- Hooks (beyond the routing skill)

### Acceptance Criteria

1. After `speculate install`, user can type `/speculate:` and see all shortcuts
2. Running `/speculate:new-plan-spec` executes the shortcut
3. Claude automatically suggests relevant shortcuts based on task context (via skill)
4. `speculate uninstall` cleanly removes the plugin
5. `speculate status` shows whether the Claude Code plugin is installed

## Stage 2: Architecture Stage

### Directory Structure Created

```
project-root/
├── .claude/
│   └── plugins/
│       └── speculate/
│           ├── .claude-plugin/
│           │   └── plugin.json
│           ├── commands/
│           │   ├── new-plan-spec.md        → symlink
│           │   ├── new-implementation-spec.md → symlink
│           │   ├── implement-spec.md       → symlink
│           │   ├── implement-beads.md      → symlink
│           │   ├── precommit-process.md    → symlink
│           │   ├── commit-code.md          → symlink
│           │   ├── create-pr-simple.md     → symlink
│           │   ├── ... (all 25+ shortcuts)
│           │   └── setup-github-cli.md     → symlink (from agent-setup)
│           └── skills/
│               └── speculate-workflow/
│                   └── SKILL.md            → generated
└── docs/
    └── general/
        ├── agent-shortcuts/
        │   ├── shortcut:new-plan-spec.md   ← source of truth
        │   └── ...
        └── agent-rules/
            ├── automatic-shortcut-triggers.md
            └── ...
```

### Generated Files

#### plugin.json

```json
{
  "name": "speculate",
  "version": "1.0.0",
  "description": "Spec-driven development workflows: planning, implementation, commits, PRs, and code review",
  "author": {
    "name": "Speculate"
  }
}
```

#### SKILL.md (Routing Skill)

```markdown
---
name: speculate-workflow
description: Spec-driven development workflow automation. Activates for feature planning,
  implementation specs, code commits, PR creation, code review, research briefs,
  architecture docs, cleanup tasks, and any development workflow that benefits from
  structured methodology.
---

# Speculate Workflow Router

Before responding to coding or development requests, check if a Speculate command applies.

## Trigger Table

| If user request involves... | Use command |
|----------------------------|-------------|
| Creating a new feature plan | /speculate:new-plan-spec |
| Creating an implementation spec | /speculate:new-implementation-spec |
| Creating implementation beads from a spec | /speculate:new-implementation-beads-from-spec |
| Creating a validation/test spec | /speculate:new-validation-spec |
| Refining or clarifying an existing spec | /speculate:refine-spec |
| Updating a spec with new information | /speculate:update-spec |
| Updating specs progress and beads | /speculate:update-specs-status |
| Implementing beads | /speculate:implement-beads |
| Implementing a spec (legacy, no beads) | /speculate:implement-spec |
| Exploratory coding / prototype / spike | /speculate:coding-spike |
| Committing code | /speculate:precommit-process then /speculate:commit-code |
| Creating a validation plan | /speculate:create-or-update-validation-plan |
| Creating a PR with validation | /speculate:create-or-update-pr-with-validation-plan |
| Creating a PR (simple) | /speculate:create-pr-simple |
| Reviewing code, specs, docs | /speculate:review-all-code-specs-docs-convex |
| Reviewing a PR | /speculate:review-pr |
| Reviewing and fixing a PR with beads | /speculate:review-pr-and-fix-with-beads |
| Research or technical investigation | /speculate:new-research-brief |
| Creating architecture documentation | /speculate:new-architecture-doc |
| Updating/revising architecture docs | /speculate:revise-architecture-doc |
| Code cleanup or refactoring | /speculate:cleanup-all |
| Removing trivial tests | /speculate:cleanup-remove-trivial-tests |
| Updating docstrings | /speculate:cleanup-update-docstrings |
| Merging from upstream | /speculate:merge-upstream |

## Common Workflow Chains

### Full Feature Flow
1. /speculate:new-plan-spec
2. /speculate:new-implementation-beads-from-spec
3. /speculate:implement-beads
4. /speculate:create-or-update-pr-with-validation-plan

### Commit Flow
1. /speculate:precommit-process
2. /speculate:commit-code

## Usage

When a matching trigger is detected:
1. Announce: "Using /speculate:[command-name]"
2. Invoke the command
3. Follow the command's instructions exactly

If no shortcut applies, proceed normally without a shortcut.
```

### New CLI Functions

#### `_setup_claude_plugin()`

```python
def _setup_claude_plugin(
    project_root: Path,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    force: bool = False,
) -> None:
    """Set up .claude/plugins/speculate/ with symlinks to shortcuts.

    Creates:
      - .claude/plugins/speculate/.claude-plugin/plugin.json
      - .claude/plugins/speculate/commands/*.md (symlinks to shortcuts)
      - .claude/plugins/speculate/skills/speculate-workflow/SKILL.md

    Symlinks are named without the 'shortcut:' prefix for clean command names.
    """
```

#### `_remove_claude_plugin()`

```python
def _remove_claude_plugin(project_root: Path) -> None:
    """Remove .claude/plugins/speculate/ directory.

    Only removes the speculate plugin, not other plugins or .claude/ content.
    """
```

#### `_generate_skill_md()`

```python
def _generate_skill_md(shortcuts: list[str]) -> str:
    """Generate the SKILL.md content based on available shortcuts.

    Reads automatic-shortcut-triggers.md for the trigger table structure
    and maps shortcut names to /speculate:command-name invocations.
    """
```

### Integration with Existing Commands

#### `install()` Changes

```python
def install(...):
    # ... existing code ...

    # .cursor/rules/
    _setup_cursor_rules(cwd, include=include, exclude=exclude, force=force)

    # NEW: .claude/plugins/speculate/
    _setup_claude_plugin(cwd, include=include, exclude=exclude, force=force)
```

#### `uninstall()` Changes

```python
def uninstall(...):
    # ... existing preview code ...

    # NEW: Check for Claude plugin
    claude_plugin = cwd / ".claude" / "plugins" / "speculate"
    if claude_plugin.exists():
        changes.append("Remove .claude/plugins/speculate/")

    # ... existing removal code ...

    # NEW: Remove Claude plugin
    _remove_claude_plugin(cwd)
```

#### `status()` Changes

```python
def status():
    # ... existing checks ...

    # NEW: Check Claude Code plugin
    claude_plugin = cwd / ".claude" / "plugins" / "speculate"
    if claude_plugin.exists():
        command_count = len(list((claude_plugin / "commands").glob("*.md")))
        print_success(f".claude/plugins/speculate/ exists ({command_count} commands)")
    else:
        print_info(".claude/plugins/speculate/ not configured")
```

### Symlink Path Calculation

For a shortcut at `docs/general/agent-shortcuts/shortcut:new-plan-spec.md`:

```python
# From: .claude/plugins/speculate/commands/new-plan-spec.md
# To:   docs/general/agent-shortcuts/shortcut:new-plan-spec.md

# Relative path (5 levels up, then into docs):
relative_target = Path("..") / ".." / ".." / ".." / ".." / \
                  "docs" / "general" / "agent-shortcuts" / source_filename

# Result: ../../../../../docs/general/agent-shortcuts/shortcut:new-plan-spec.md
```

### Shortcut Sources

The CLI will collect shortcuts from multiple directories:

| Source Directory | Command Prefix | Example |
|-----------------|----------------|---------|
| `docs/general/agent-shortcuts/` | (none) | `/speculate:new-plan-spec` |
| `docs/general/agent-setup/` | (none) | `/speculate:setup-github-cli` |
| `docs/project/agent-shortcuts/` | (none) | Project-specific shortcuts |

All are flattened into the `commands/` directory. Project shortcuts override general
shortcuts with the same name (after stripping `shortcut:` prefix).

## Stage 3: Refine Architecture

### Reusable Components

| Component | Source | Reuse |
|-----------|--------|-------|
| Symlink creation | `_setup_cursor_rules()` | Pattern reused, adjusted for plugin structure |
| Pattern matching | `_matches_patterns()` | Reused directly |
| Directory removal | `_remove_cursor_rules()` | Pattern reused for plugin removal |
| Atomic file writes | `strif.atomic_output_file` | Used for generated files |

### Code to Generate vs Template

| Content | Approach | Rationale |
|---------|----------|-----------|
| `plugin.json` | Generate in code | Simple, rarely changes |
| `SKILL.md` | Generate based on trigger file | Maps triggers to new command names |
| Commands | Symlinks | Zero duplication, single source of truth |

### Error Handling

| Scenario | Handling |
|----------|----------|
| No shortcuts found | Warning, skip plugin creation |
| Symlink already exists | Remove and recreate (if `--force`) or skip |
| `.claude/` doesn't exist | Create it |
| `docs/general/agent-shortcuts/` missing | Warning, skip plugin |
| Permission errors | Error with clear message |

### Testing Considerations

1. **Unit tests**: Mock filesystem for symlink creation
2. **Integration tests**: Create temp directories, verify structure
3. **Manual verification**: Run in real project, test `/speculate:` tab completion

---

## Detailed Implementation

This section provides the complete implementation details based on analysis of the
existing CLI codebase (`cli/src/speculate/cli/cli_commands.py`).

### New Constants

Add to top of `cli_commands.py`:

```python
# Claude Code plugin configuration
CLAUDE_PLUGIN_NAME = "speculate"
CLAUDE_PLUGIN_DIR = f".claude/plugins/{CLAUDE_PLUGIN_NAME}"
CLAUDE_PLUGIN_VERSION = "1.0.0"
CLAUDE_PLUGIN_DESCRIPTION = (
    "Spec-driven development workflows: planning, implementation, commits, PRs, and code review"
)
```

### Function: `_setup_claude_plugin()`

Full implementation following the pattern of `_setup_cursor_rules()`:

```python
def _setup_claude_plugin(
    project_root: Path,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    force: bool = False,
) -> None:
    """Set up .claude/plugins/speculate/ with symlinks to shortcuts.

    Collects shortcuts from:
      - docs/general/agent-shortcuts/shortcut:*.md
      - docs/general/agent-setup/shortcut:*.md
      - docs/project/agent-shortcuts/shortcut:*.md (if exists, takes precedence)

    Creates:
      - .claude/plugins/speculate/.claude-plugin/plugin.json
      - .claude/plugins/speculate/commands/*.md (symlinks)
      - .claude/plugins/speculate/skills/speculate-workflow/SKILL.md

    Symlinks strip the 'shortcut:' prefix for clean command names.
    """
    plugin_dir = project_root / CLAUDE_PLUGIN_DIR
    commands_dir = plugin_dir / "commands"
    skills_dir = plugin_dir / "skills" / "speculate-workflow"
    manifest_dir = plugin_dir / ".claude-plugin"

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

    # Generate plugin.json
    plugin_json = _generate_plugin_json()
    plugin_json_path = manifest_dir / "plugin.json"
    if not plugin_json_path.exists() or force:
        with atomic_output_file(plugin_json_path) as temp_path:
            Path(temp_path).write_text(plugin_json)
        print_success(f"Generated {CLAUDE_PLUGIN_DIR}/.claude-plugin/plugin.json")

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

        # Calculate relative path: commands/ is 5 levels deep from project root
        # .claude/plugins/speculate/commands/file.md -> docs/general/agent-shortcuts/shortcut:file.md
        relative_target = (
            Path("..") / ".." / ".." / ".." / ".." / relative_dir / source_path.name
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
```

### Function: `_remove_claude_plugin()`

```python
def _remove_claude_plugin(project_root: Path) -> None:
    """Remove .claude/plugins/speculate/ directory.

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
```

### Function: `_generate_plugin_json()`

```python
def _generate_plugin_json() -> str:
    """Generate plugin.json content for the Speculate plugin."""
    import json

    plugin_data = {
        "name": CLAUDE_PLUGIN_NAME,
        "version": CLAUDE_PLUGIN_VERSION,
        "description": CLAUDE_PLUGIN_DESCRIPTION,
        "author": {"name": "Speculate"},
    }
    return json.dumps(plugin_data, indent=2) + "\n"
```

### Function: `_generate_skill_md()`

```python
def _generate_skill_md(shortcut_names: list[str]) -> str:
    """Generate SKILL.md content for the routing skill.

    Creates a skill that Claude Code will automatically invoke based on
    semantic matching, directing it to use the appropriate /speculate:* command.
    """
    # Build trigger table from shortcut names
    # Maps common patterns to commands
    trigger_mappings = {
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

    # Build trigger table rows for available shortcuts
    trigger_rows = []
    for name in sorted(shortcut_names):
        stem = name.replace(".md", "")
        description = trigger_mappings.get(stem, f"Using {stem}")
        trigger_rows.append(f"| {description} | /speculate:{stem} |")

    trigger_table = "\n".join(trigger_rows)

    return f'''---
name: speculate-workflow
description: Spec-driven development workflow automation. Activates for feature planning,
  implementation specs, code commits, PR creation, code review, research briefs,
  architecture docs, cleanup tasks, and any development workflow that benefits from
  structured methodology.
---

# Speculate Workflow Router

Before responding to coding or development requests, check if a Speculate command applies.

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

## Usage

When a matching trigger is detected:
1. Announce: "Using /speculate:[command-name]"
2. Invoke the command
3. Follow the command's instructions exactly

If no shortcut applies, proceed normally without a shortcut.
'''
```

### Modifications to `install()`

Add after the existing `_setup_cursor_rules()` call (around line 250):

```python
def install(...) -> None:
    # ... existing code through _setup_cursor_rules() ...

    # .cursor/rules/
    _setup_cursor_rules(cwd, include=include, exclude=exclude, force=force)

    # NEW: .claude/plugins/speculate/
    _setup_claude_plugin(cwd, include=include, exclude=exclude, force=force)

    # ... rest of existing code ...
```

### Modifications to `uninstall()`

Add to the preview section and removal section:

```python
def uninstall(force: bool = False) -> None:
    # ... existing preview code ...

    # NEW: Check for Claude plugin
    claude_plugin = cwd / CLAUDE_PLUGIN_DIR
    if claude_plugin.exists():
        command_count = len(list((claude_plugin / "commands").glob("*.md")))
        changes.append(f"Remove {CLAUDE_PLUGIN_DIR}/ ({command_count} commands)")

    # ... after confirmation ...

    # NEW: Remove Claude plugin (after existing removals)
    _remove_claude_plugin(cwd)
```

### Modifications to `status()`

Add after the existing tool config checks (around line 330):

```python
def status() -> None:
    # ... existing checks ...

    # Check tool configs (existing code)
    for name, path in [
        ("CLAUDE.md", cwd / "CLAUDE.md"),
        ("AGENTS.md", cwd / "AGENTS.md"),
        (".cursor/rules/", cwd / ".cursor" / "rules"),
    ]:
        # ... existing logic ...

    # NEW: Check Claude Code plugin
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
```

### Import Additions

Add `shutil` import if not already present (needed for `_remove_claude_plugin`):

```python
import shutil  # Already imported at line 11
```

Add `json` import for `_generate_plugin_json`:

```python
import json  # Add to imports
```

### File Changes Summary

| File | Changes |
|------|---------|
| `cli_commands.py` | Add 4 new constants, 4 new functions (~150 lines), modify 3 functions |
| `cli_main.py` | No changes needed (install already passes include/exclude/force) |
| `cli_ui.py` | No changes needed |

### Implementation Order

1. Add constants at top of file
2. Add `_generate_plugin_json()` function
3. Add `_generate_skill_md()` function
4. Add `_setup_claude_plugin()` function
5. Add `_remove_claude_plugin()` function
6. Modify `install()` to call `_setup_claude_plugin()`
7. Modify `uninstall()` to call `_remove_claude_plugin()`
8. Modify `status()` to check plugin status
9. Add tests

## Resolved Decisions

| # | Question | Decision | Rationale |
|---|----------|----------|-----------|
| 1 | Plugin vs standalone commands? | Plugin | Namespacing (`/speculate:`) preserves brand, bundles skill |
| 2 | Copy files or symlink? | Symlink | Single source of truth, updates automatically |
| 3 | Handle `shortcut:` prefix? | Strip from symlink name | Clean command names |
| 4 | How to auto-trigger? | Routing skill | Claude Code's semantic matching activates skill |
| 5 | Where does skill get content? | Generate from `automatic-shortcut-triggers.md` | Stays in sync with existing trigger table |
| 6 | Include agent-rules in plugin? | No (v1) | Commands are primary; rules work via CLAUDE.md |
| 7 | Include agent-setup shortcuts? | Yes | Useful setup commands like `setup-github-cli` |

---

## Open Questions

### Implementation Questions

1. **Skill description optimization**: How specific should the routing skill's description
   be to ensure reliable activation without false positives? Need to test with real usage.

2. **Shortcut format compatibility**: Do existing shortcuts need any modifications to work
   well as Claude Code commands? (e.g., `@` references, relative paths)

3. **Update workflow**: When `speculate update` pulls new shortcuts, should the plugin be
   automatically regenerated? What about symlink validity checking?

4. **Conflict handling**: What happens if a user has their own `.claude/plugins/speculate/`
   or commands with the same names?

### Broader Questions (from Research Brief)

5. **Cross-platform skill translation**: Could shortcuts be automatically adapted to work
   as Cursor rules (with `alwaysApply`) in addition to Claude Code commands?

6. **Skill versioning**: How should we version the generated plugin when shortcuts change?
   Should `plugin.json` version track the Speculate CLI version?

7. **Personal vs project installation**: Should we support installing to `~/.claude/plugins/`
   for cross-project availability? What are the trade-offs?

8. **Marketplace distribution**: Is it worth publishing Speculate to a Claude Code marketplace
   for easier discovery, or is CLI installation sufficient?

---

## v1.1: Priority 1 Enhancements (Essential Before Merge)

Based on ecosystem review comparing with popular plugins (Superpowers, cassler/awesome-claude-code-setup,
jeremylongshore/claude-code-plugins-plus-skills), these improvements align Speculate with best practices.

### v1.1 Features

| # | Feature | Description | Status |
|---|---------|-------------|--------|
| 1 | **Dynamic version sync** | Plugin version should match CLI version | 🔲 TODO |
| 2 | **Plugin README** | Add README.md to generated plugin for discoverability | 🔲 TODO |
| 3 | **Token budget docs** | Document token overhead in SKILL.md | 🔲 TODO |
| 4 | **Repository/homepage** | Add repository and homepage URLs to plugin.json | 🔲 TODO |

### v1.1 Implementation Details

#### 1. Dynamic Version Sync

**Problem**: Current implementation uses hardcoded `CLAUDE_PLUGIN_VERSION = "1.0.0"`.

**Solution**: Use CLI version dynamically:

```python
def _generate_plugin_json() -> str:
    """Generate plugin.json content for the Speculate plugin."""
    from importlib.metadata import version as get_version

    try:
        cli_version = get_version("speculate-cli")
    except Exception:
        cli_version = "0.0.0"

    plugin_data = {
        "name": CLAUDE_PLUGIN_NAME,
        "version": cli_version,  # Dynamic instead of hardcoded
        "description": CLAUDE_PLUGIN_DESCRIPTION,
        "author": {"name": "Speculate"},
        "repository": "https://github.com/jlevy/speculate",
        "homepage": "https://github.com/jlevy/speculate",
    }
    return json.dumps(plugin_data, indent=2) + "\n"
```

**Files**: `cli/src/speculate/cli/cli_commands.py`

#### 2. Plugin README Generation

**Problem**: No README in generated plugin makes it harder to understand what's installed.

**Solution**: Generate `README.md` in plugin root:

```python
def _generate_plugin_readme(command_count: int, skill_name: str) -> str:
    """Generate README.md content for the Speculate plugin."""
    return dedent(f"""
        # Speculate Plugin for Claude Code

        This plugin provides spec-driven development workflows for Claude Code.

        ## What's Included

        - **{command_count} commands**: Type `/speculate:` to see available commands
        - **1 skill**: `{skill_name}` for automatic workflow detection

        ## Usage

        Commands are invoked as `/speculate:command-name`. For example:
        - `/speculate:new-plan-spec` - Create a feature plan
        - `/speculate:implement-beads` - Implement work items
        - `/speculate:commit-code` - Commit with pre-commit checks

        The routing skill automatically suggests relevant commands based on your task.

        ## Source

        Commands are symlinked from `docs/general/agent-shortcuts/`. Edit the source
        files to customize behavior.

        ## More Information

        - Repository: https://github.com/jlevy/speculate
        - CLI: `pip install speculate-cli`
        """).strip() + "\n"
```

**Files**: `cli/src/speculate/cli/cli_commands.py`

**Directory Structure Update**:
```
.claude/plugins/speculate/
├── README.md                    ← NEW
├── .claude-plugin/
│   └── plugin.json
├── commands/
└── skills/
```

#### 3. Token Budget Documentation

**Problem**: Users don't know how much context the plugin adds.

**Solution**: Add token budget section to generated SKILL.md:

```markdown
## Token Budget

This skill adds approximately 400-500 tokens to context when activated.
The trigger table and workflow chains are designed to be concise while
providing clear routing guidance.

To minimize token usage:
- The skill only activates when semantic matching triggers it
- Detailed command instructions are in the command files (loaded on demand)
- Keep your prompts focused on the task at hand
```

**Files**: `cli/src/speculate/cli/cli_commands.py` (update `_generate_skill_md()`)

#### 4. Repository/Homepage in plugin.json

**Problem**: Missing repository and homepage fields in plugin.json.

**Solution**: Already shown in item 1 above - add to `_generate_plugin_json()`.

---

## v2: Priority 2 Enhancements (Future Release)

These features add significant value but require more implementation effort.

### v2 Features

| # | Feature | Description | Status |
|---|---------|-------------|--------|
| 1 | **SessionStart hook** | Auto-display welcome message on session start | 🔲 TODO |
| 2 | **Personal installation** | Support `--global` flag to install to `~/.claude/plugins/` | 🔲 TODO |
| 3 | **PostToolUse hook** | Optional formatting hook after file edits | 🔲 TODO |
| 4 | **Cross-platform support** | Generate Cursor rules from skills (with alwaysApply) | 🔲 TODO |
| 5 | **Symlink agent-rules** | Include agent-rules as reference content in plugin | 🔲 TODO |

### v2 Implementation Details

#### 1. SessionStart Hook

**Purpose**: Display welcome message when Claude Code starts, showing available commands.

**Implementation**:

```python
def _generate_hooks_json() -> str:
    """Generate hooks.json for lifecycle automation."""
    hooks_data = {
        "hooks": {
            "SessionStart": [{
                "matcher": "*",
                "hooks": [{
                    "type": "command",
                    "command": "echo '📋 Speculate workflows available. Type /speculate: to see commands.'"
                }]
            }]
        }
    }
    return json.dumps(hooks_data, indent=2) + "\n"
```

**Directory Structure Update**:
```
.claude/plugins/speculate/
├── hooks/
│   └── hooks.json              ← NEW
├── ...
```

**Files**: `cli/src/speculate/cli/cli_commands.py`

#### 2. Personal Installation (`--global`)

**Purpose**: Allow cross-project installation to `~/.claude/plugins/speculate/`.

**CLI Changes**:
```python
def install(
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    force: bool = False,
    global_install: bool = False,  # NEW
) -> None:
    """Generate tool configs for Cursor, Claude Code, and Codex.

    ...existing docstring...

    Use --global to install the Claude Code plugin to ~/.claude/plugins/
    for cross-project availability.
    """
```

**Implementation Considerations**:
- When `--global`, install to `~/.claude/plugins/speculate/`
- Symlinks must use absolute paths (can't use relative paths to project docs)
- Alternative: Copy files instead of symlink for global install
- Need to handle updates: `speculate update --global`

**Files**:
- `cli/src/speculate/cli/cli_commands.py`
- `cli/src/speculate/cli/cli_main.py` (add `--global` option)

#### 3. PostToolUse Hook (Optional)

**Purpose**: Auto-format files after Claude edits them.

**Implementation**:
```python
def _generate_hooks_json(include_formatting: bool = False) -> str:
    hooks_data = {
        "hooks": {
            "SessionStart": [/* ... */],
        }
    }

    if include_formatting:
        hooks_data["hooks"]["PostToolUse"] = [{
            "matcher": "Edit|Write",
            "hooks": [{
                "type": "command",
                "command": "if command -v prettier &> /dev/null; then prettier --write \"$CC_TOOL_ARG_FILE_PATH\" 2>/dev/null || true; fi"
            }]
        }]

    return json.dumps(hooks_data, indent=2) + "\n"
```

**CLI Option**: `speculate install --with-format-hook`

#### 4. Cross-Platform Support

**Purpose**: Generate Cursor rules from shortcuts for teams using both tools.

**Implementation**: Create `.cursor/commands/` directory with shortcuts that have
`alwaysApply: false` so they're available but not auto-triggered.

**Complexity**: Medium - requires adapting markdown format for Cursor's `.mdc` format.

#### 5. Symlink Agent-Rules to Plugin

**Purpose**: Include agent-rules as context available to the routing skill.

**Implementation**: Add `reference/` directory in plugin with symlinks to agent-rules:

```
.claude/plugins/speculate/
├── reference/                   ← NEW
│   ├── automatic-shortcut-triggers.md → symlink
│   ├── general-rules.md → symlink
│   └── ...
```

The routing skill can then reference these for context.

---

## v3+: Future Enhancements (Backlog)

These are tracked for future consideration but not planned for immediate implementation.

| # | Feature | Description |
|---|---------|-------------|
| 1 | **Marketplace listing** | Publish to `ccplugins/awesome-claude-code-plugins` |
| 2 | **MCP server** | Expose Speculate CLI as MCP tools for Claude Code |
| 3 | **Subagents** | Specialized agents (spec-writer, code-reviewer, bead-implementer) |
| 4 | **Domain skills** | Deep skills beyond routing (spec-driven-planning, bead-tracking) |
| 5 | **Skill versioning** | Version skills independently for backwards compatibility |

---

## Status

### v1: Core Implementation ✅ Complete (2026-01-04)

All "Must Have" features have been implemented:
- Added `_setup_claude_plugin()` and `_remove_claude_plugin()` functions
- Integrated into `install()`, `uninstall()`, and `status()` commands
- Added comprehensive tests (22 new test cases)
- Commit: `6fd0f6d` on branch `claude/explore-repo-structure-KkIRu`

See beads tracking: All 11 beads (speculate-tj4 epic + 10 task beads) are closed.

### v1.1: Priority 1 Enhancements ✅ Complete (2026-01-04)

**Epic**: `speculate-nz9` - Claude Code plugin v1.1 enhancements

| Bead ID | Task | Status |
|---------|------|--------|
| `speculate-dc9` | Implement dynamic version sync for plugin.json | ✅ Done |
| `speculate-j58` | Generate README.md in plugin directory | ✅ Done |
| `speculate-35s` | Add token budget documentation to SKILL.md | ✅ Done |
| `speculate-xbc` | Add tests for v1.1 plugin enhancements | ✅ Done |

**Implementation details:**
- `_get_plugin_version()` reads version from importlib.metadata
- `_generate_plugin_readme()` creates informative README.md
- Token budget section added to `_generate_skill_md()`
- Repository/homepage URLs added to plugin.json
- 13 new test cases for v1.1 features

### v2: Priority 2 Enhancements ✅ Complete (2026-01-04)

**Epic**: `speculate-j49` - Claude Code plugin v2 enhancements

| Bead ID | Task | Status |
|---------|------|--------|
| `speculate-qhg` | Implement SessionStart hook generation | ✅ Done |
| `speculate-hr8` | Implement --global flag for personal installation | ✅ Done |
| `speculate-azw` | Implement optional PostToolUse formatting hook | 🔲 Deferred |
| `speculate-hos` | Add cross-platform Cursor rules generation | 🔲 Deferred |
| `speculate-3we` | Symlink agent-rules to plugin reference directory | ✅ Done |
| `speculate-5wo` | Add tests for v2 plugin enhancements | ✅ Done |

**Implementation details:**
- `_generate_hooks_json()` creates SessionStart hook
- `--global` flag on `install` and `uninstall` commands
- `_setup_global_claude_plugin()` installs to `~/.claude/plugins/`
- Reference symlinks to agent-rules in plugin directory
- Status shows both project and global plugin status
- 7 new test cases for v2 features

**Deferred to v3:**
- PostToolUse formatting hook (requires more research on best practices)
- Cross-platform Cursor rules generation (significant complexity)
