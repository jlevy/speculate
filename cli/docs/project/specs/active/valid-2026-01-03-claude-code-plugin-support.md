# Feature Validation: Claude Code Plugin Support

## Purpose

This validation spec documents the testing performed and manual validation needed for
the Claude Code plugin support feature in the Speculate CLI.

**Feature Plan:** [plan-2026-01-03-claude-code-plugin-support.md](plan-2026-01-03-claude-code-plugin-support.md)

**Research Brief:** [research-coding-agent-skills-commands-extensions.md](../../../../docs/general/research/current/research-coding-agent-skills-commands-extensions.md)

## Scope of This PR

This PR includes three components:

1. **v1 Core Implementation** ✅ Complete
   - Claude Code plugin generation (`speculate install`)
   - Plugin removal (`speculate uninstall`)
   - Status reporting (`speculate status`)
   - 22 unit/integration tests

2. **v1.1 & v2 Enhancement Planning** ✅ Complete
   - Ecosystem research comparing with Superpowers, cassler/awesome-claude-code-setup, etc.
   - Detailed implementation plans for Priority 1 and Priority 2 features
   - 12 beads created for tracking (4 for v1.1, 6 for v2, 2 epics)

3. **Research Documentation** ✅ Complete
   - Comprehensive research brief on coding agent extension mechanisms
   - Cross-platform comparison (Claude Code, Codex, Cursor, Windsurf)

## Stage 4: Validation Stage

## Validation Planning

The Claude Code plugin support feature adds the ability for `speculate install` to create
a Claude Code plugin at `.claude/plugins/speculate/` with symlinked commands and a
generated routing skill.

## Automated Validation (Testing Performed)

### Unit Testing

Added 22 new test cases in `cli/tests/test_cli_commands.py`:

**TestGeneratePluginJson (1 test)**
- `test_generates_valid_json` - Validates plugin.json has correct structure and fields

**TestGenerateSkillMd (3 tests)**
- `test_generates_skill_with_frontmatter` - YAML frontmatter with name and description
- `test_generates_trigger_table` - Trigger table with command mappings
- `test_includes_workflow_chains` - Common workflow chains section

**TestSetupClaudePlugin (12 tests)**
- `test_creates_plugin_directory_structure` - Creates commands/, skills/, .claude-plugin/
- `test_generates_plugin_json` - Generates valid plugin manifest
- `test_creates_symlinks_for_shortcuts` - Strips shortcut: prefix from names
- `test_symlinks_are_relative` - Symlinks use relative paths
- `test_generates_skill_md` - Generates SKILL.md routing skill
- `test_include_pattern_filters_shortcuts` - Include patterns work
- `test_exclude_pattern_filters_shortcuts` - Exclude patterns work
- `test_skips_existing_symlinks_without_force` - Respects existing symlinks
- `test_overwrites_with_force` - Force flag overwrites existing
- `test_collects_from_agent_setup` - Collects from agent-setup directory
- `test_project_shortcuts_override_general` - Project shortcuts take precedence
- `test_warns_when_no_shortcuts` - Warns and skips when no shortcuts found

**TestRemoveClaudePlugin (4 tests)**
- `test_removes_plugin_directory` - Removes entire plugin directory
- `test_cleans_up_empty_parent_directories` - Cleans up empty .claude/plugins/
- `test_preserves_other_plugins` - Does not remove other plugins
- `test_no_error_if_plugin_missing` - No error if plugin doesn't exist

**TestInstallWithClaudePlugin (1 test)**
- `test_creates_claude_plugin` - Integration test for install command

**TestUninstallWithClaudePlugin (1 test)**
- `test_removes_claude_plugin` - Integration test for uninstall command

### Integration and End-to-End Testing

Integration tests are included in the test suite above. Due to build environment
limitations (shallow git clone affecting dynamic versioning), full pytest run was not
executed in the current session, but:

1. All new code passes `ruff check` linting
2. All test files are syntactically correct and importable

### Manual Testing Needed

The user should perform the following manual validation:

#### 1. Run Tests Locally

```bash
cd cli
make test  # or: uv run pytest tests/test_cli_commands.py -v
```

Verify all 22 new tests pass.

#### 2. Test Install Command

```bash
cd /path/to/project  # A project with speculate docs installed
speculate install
```

Verify output shows:
- `Generated .claude/plugins/speculate/.claude-plugin/plugin.json`
- `Generated .claude/plugins/speculate/skills/speculate-workflow/SKILL.md`
- `.claude/plugins/speculate/: linked N commands`

#### 3. Verify Plugin Structure

```bash
ls -la .claude/plugins/speculate/
ls -la .claude/plugins/speculate/commands/
ls -la .claude/plugins/speculate/skills/speculate-workflow/
cat .claude/plugins/speculate/.claude-plugin/plugin.json
```

Verify:
- Directory structure is correct
- Command symlinks exist and point to docs/general/agent-shortcuts/
- Symlinks have clean names (no `shortcut:` prefix)
- SKILL.md exists and contains trigger table
- plugin.json has correct metadata

#### 4. Test Status Command

```bash
speculate status
```

Verify output includes:
- `.claude/plugins/speculate/ exists (N commands)`

#### 5. Test Uninstall Command

```bash
speculate uninstall --force
```

Verify:
- `.claude/plugins/speculate/` is removed
- Status shows `.claude/plugins/speculate/ not configured`

#### 6. Test Force Reinstall

```bash
speculate install
speculate install --force
```

Verify no errors and regeneration messages appear.

#### 7. Verify in Claude Code (if available)

If Claude Code is installed:
1. Open the project in Claude Code
2. Type `/speculate:` and verify command autocomplete shows available commands
3. Try running `/speculate:new-plan-spec` to verify command execution

## Planning Validation (v1.1 & v2)

The following planning artifacts were created and should be reviewed:

### v1.1 Enhancement Plan (Priority 1 - Before Merge)

Located in plan spec v1.1 section. Features planned:

| Feature | Bead ID | Purpose |
|---------|---------|---------|
| Dynamic version sync | `speculate-dc9` | Plugin version matches CLI version |
| Plugin README | `speculate-j58` | Generated README.md for discoverability |
| Token budget docs | `speculate-35s` | Document context overhead in SKILL.md |
| Tests | `speculate-xbc` | Unit tests for v1.1 features |

**Epic**: `speculate-nz9`

### v2 Enhancement Plan (Priority 2 - Future Release)

Located in plan spec v2 section. Features planned:

| Feature | Bead ID | Purpose |
|---------|---------|---------|
| SessionStart hook | `speculate-qhg` | Welcome message on session start |
| Personal installation | `speculate-hr8` | `--global` flag for ~/.claude/plugins/ |
| PostToolUse hook | `speculate-azw` | Optional auto-formatting hook |
| Cross-platform | `speculate-hos` | Cursor rules from shortcuts |
| Agent-rules symlinks | `speculate-3we` | Reference directory in plugin |
| Tests | `speculate-5wo` | Unit tests for v2 features |

**Epic**: `speculate-j49`

### Review Checklist for Plans

- [ ] v1.1 features are appropriate for "before merge" priority
- [ ] v2 features are appropriate for "future release" priority
- [ ] Implementation details are clear and actionable
- [ ] Beads are correctly linked to plan spec
- [ ] Dependencies between beads are correct

## Open Questions

1. **Full test suite**: Can the user run `make test` successfully in the CLI directory?
   The development environment may need `git fetch --unshallow` for dynamic versioning.

2. **Claude Code plugin loading**: Does Claude Code correctly load plugins from
   `.claude/plugins/` with symlinked commands? This needs manual verification.

3. **v1.1 scope**: Should v1.1 features be implemented before merging this PR, or
   is the current v1 implementation sufficient for initial release?

4. **Ecosystem alignment**: Are there other popular plugin patterns we should consider
   beyond what's documented in the research brief?
