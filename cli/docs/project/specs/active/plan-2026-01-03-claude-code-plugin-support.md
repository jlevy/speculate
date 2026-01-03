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

- [ ] Create `.claude/plugins/speculate/` directory structure
- [ ] Generate `.claude/plugins/speculate/.claude-plugin/plugin.json`
- [ ] Symlink all shortcuts from `docs/general/agent-shortcuts/shortcut:*.md` to commands
- [ ] Generate routing skill at `.claude/plugins/speculate/skills/speculate-workflow/SKILL.md`
- [ ] Update `speculate install` to call new `_setup_claude_plugin()` function
- [ ] Update `speculate uninstall` to remove `.claude/plugins/speculate/`
- [ ] Update `speculate status` to show Claude Code plugin status
- [ ] Support `--include` and `--exclude` patterns for shortcuts

**Nice to Have (v2):**

- [ ] Symlink agent-rules as well (for context in skill instructions)
- [ ] Support for agent-setup shortcuts
- [ ] Personal installation to `~/.claude/plugins/`

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

**Next Step:** Review this plan, then create implementation spec at
`impl-2026-01-03-claude-code-plugin-support.md` with detailed phases and tasks.
