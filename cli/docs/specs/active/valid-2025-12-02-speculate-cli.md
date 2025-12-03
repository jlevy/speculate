# Feature Validation: Speculate CLI

## Purpose

This is a validation spec, used to list post-testing validation that must be performed
by the user to confirm the feature implementation and testing is adequate.

**Feature Plan:** [plan-2025-12-02-speculate-cli.md](plan-2025-12-02-speculate-cli.md)

**Implementation Plan:**
[impl-2025-12-02-speculate-cli.md](impl-2025-12-02-speculate-cli.md)

## Stage 4: Validation Stage

## Validation Planning

The Speculate CLI has been implemented through Phase 4 (Testing and Polish).
Phase 5 (Publishing) remains for PyPI release.

## Automated Validation (Testing Performed)

**Total: 41 tests passing**

All tests run via `make test` in the `cli/` directory.

### Unit Testing

Located in `cli/tests/test_cli_helpers.py` (12 tests):

| Test | Description |
| --- | --- |
| `TestGetDirStats::test_empty_directory` | Empty dir returns 0 files, 0 bytes |
| `TestGetDirStats::test_single_file` | Single file counted correctly |
| `TestGetDirStats::test_nested_files` | Nested files counted recursively |
| `TestMatchesPatterns::test_no_patterns_matches_all` | No patterns matches everything |
| `TestMatchesPatterns::test_include_pattern_matches` | Include pattern filters correctly |
| `TestMatchesPatterns::test_exclude_pattern_excludes` | Exclude pattern filters correctly |
| `TestMatchesPatterns::test_include_and_exclude_together` | Combined patterns work |
| `TestMatchesPatterns::test_double_star_pattern` | `**` normalized to `*` |
| `TestEnsureSpeculateHeader::test_creates_new_file` | Creates file with header |
| `TestEnsureSpeculateHeader::test_prepends_to_existing_file` | Prepends to existing |
| `TestEnsureSpeculateHeader::test_idempotent_with_marker` | Doesn't duplicate header |
| `TestEnsureSpeculateHeader::test_header_format` | Header contains required text |

Located in `cli/tests/test_cli_commands.py` (13 tests):

| Test | Description |
| --- | --- |
| `TestUpdateSpeculateSettings::test_creates_settings_file` | Creates `.speculate/settings.yml` |
| `TestUpdateSpeculateSettings::test_updates_existing_settings` | Preserves existing keys |
| `TestUpdateSpeculateSettings::test_reads_docs_version_from_copier_answers` | Reads `_commit` |
| `TestSetupCursorRules::test_creates_cursor_rules_directory` | Creates `.cursor/rules/` |
| `TestSetupCursorRules::test_creates_symlinks_for_md_files` | Creates `.mdc` symlinks |
| `TestSetupCursorRules::test_symlinks_are_relative` | Symlinks use relative paths |
| `TestSetupCursorRules::test_include_pattern_filters_rules` | Include pattern works |
| `TestSetupCursorRules::test_exclude_pattern_filters_rules` | Exclude pattern works |
| `TestSetupCursorRules::test_warns_when_rules_dir_missing` | Warns gracefully |
| `TestInstallCommand::test_fails_without_docs_directory` | Fails with exit code 1 |
| `TestInstallCommand::test_creates_all_configs` | Creates all tool configs |
| `TestStatusCommand::test_fails_without_development_md` | Fails with exit code 1 |
| `TestStatusCommand::test_succeeds_with_development_md` | Succeeds when present |

### Integration and End-to-End Testing

Located in `cli/tests/test_integration.py` (15 tests):

Uses local repo as template (`--template /path/to/speculate`).

| Test | Description |
| --- | --- |
| `TestInitWithLocalTemplate::test_init_creates_docs_directory` | Creates `docs/` |
| `TestInitWithLocalTemplate::test_init_copies_docs_overview` | Copies `docs-overview.md` |
| `TestInitWithLocalTemplate::test_init_copies_agent_rules` | Copies agent rules |
| `TestInitWithLocalTemplate::test_init_auto_runs_install` | Auto-creates tool configs |
| `TestInstallCommand::test_install_creates_claude_md` | Creates CLAUDE.md with header |
| `TestInstallCommand::test_install_creates_agents_md` | Creates AGENTS.md with header |
| `TestInstallCommand::test_install_creates_cursor_symlinks` | Creates `.mdc` symlinks |
| `TestInstallCommand::test_install_with_include_pattern` | Filters with `--include` |
| `TestInstallCommand::test_install_with_exclude_pattern` | Filters with `--exclude` |
| `TestInstallCommand::test_install_updates_settings_yml` | Updates settings file |
| `TestStatusCommand::test_status_shows_template_info` | Shows version info |
| `TestStatusCommand::test_status_fails_without_development_md` | Fails appropriately |
| `TestStatusCommand::test_status_shows_tool_configs` | Shows config status |
| `TestFullWorkflow::test_complete_workflow` | Full init→install→status |
| `TestFullWorkflow::test_workflow_with_existing_claude_md` | Preserves existing content |

### Manual Testing Needed

The following manual validation steps should be performed by the user:

#### 1. CLI Help and Version Output

Verify help text formatting and content is clear:

```bash
cd cli
uv run speculate --help
uv run speculate --version
uv run speculate init --help
uv run speculate update --help
uv run speculate install --help
uv run speculate status --help
```

**Check:**

- [ ] All help text is readable and well-formatted

- [ ] Version shows correctly (e.g., `speculate v0.0.1.dev...`)

- [ ] Subcommand descriptions are accurate

#### 2. Init Command with Local Template

Test initializing a new project using the local repo as template:

```bash
# Create a fresh test directory
mkdir /tmp/test-speculate && cd /tmp/test-speculate

# Run init with local template
uv run --project /path/to/speculate/cli speculate init --template /path/to/speculate
```

**Check:**

- [ ] Prompts for confirmation before copying

- [ ] Shows files being copied

- [ ] Creates `docs/` directory with correct structure

- [ ] Creates `docs/development.md` from sample template

- [ ] Auto-runs install (creates CLAUDE.md, AGENTS.md, .cursor/rules/)

- [ ] Shows success message with file count and size

- [ ] Shows “Required next step” reminder about development.md

#### 3. Install Command Output

Run install separately to verify output:

```bash
cd /tmp/test-speculate
uv run --project /path/to/speculate/cli speculate install
```

**Check:**

- [ ] Shows “Installing tool configurations …” header

- [ ] Shows checkmarks for each config created/updated

- [ ] Shows number of rules linked to .cursor/rules/

#### 4. Status Command Output

Run status to verify display:

```bash
cd /tmp/test-speculate
uv run --project /path/to/speculate/cli speculate status
```

**Check:**

- [ ] Shows template version (or “not initialized” appropriately)

- [ ] Shows last install timestamp and CLI version

- [ ] Shows docs/ stats (file count, size)

- [ ] Shows development.md status (green check or red X)

- [ ] Shows tool config status for CLAUDE.md, AGENTS.md, .cursor/rules/

#### 5. Verify Generated Files

Inspect the generated files manually:

```bash
cd /tmp/test-speculate

# Check CLAUDE.md
cat CLAUDE.md
# Should have speculate header at top

# Check AGENTS.md
cat AGENTS.md
# Should have speculate header at top

# Check .cursor/rules/ symlinks
ls -la .cursor/rules/
# Should show .mdc symlinks pointing to ../../docs/general/agent-rules/*.md

# Check .speculate/settings.yml
cat .speculate/settings.yml
# Should have last_update, last_cli_version
```

**Check:**

- [ ] CLAUDE.md has header with “Speculate project structure” marker

- [ ] AGENTS.md has header with “Speculate project structure” marker

- [ ] .cursor/rules/ has .mdc symlinks (not copies)

- [ ] Symlinks are relative paths

- [ ] .speculate/settings.yml has correct timestamps

#### 6. Idempotency Test

Run install multiple times to verify idempotency:

```bash
cd /tmp/test-speculate

# Add content to CLAUDE.md
echo -e "\n\n# My Custom Rules\nSome custom content here." >> CLAUDE.md

# Run install again
uv run --project /path/to/speculate/cli speculate install

# Check CLAUDE.md wasn't duplicated
cat CLAUDE.md
```

**Check:**

- [ ] Header appears only once (not duplicated)

- [ ] Custom content is preserved

- [ ] Shows “already configured” message for files with marker

#### 7. Include/Exclude Patterns

Test filtering with patterns:

```bash
cd /tmp/test-speculate

# Clear cursor rules
rm .cursor/rules/*.mdc

# Install only general-* rules
uv run --project /path/to/speculate/cli speculate install --include "general-*.md"
ls .cursor/rules/

# Clear and test exclude
rm .cursor/rules/*.mdc
uv run --project /path/to/speculate/cli speculate install --exclude "convex-*.md"
ls .cursor/rules/
```

**Check:**

- [ ] `--include` only links matching files

- [ ] `--exclude` skips matching files

- [ ] Output shows count of skipped files

#### 8. Error Handling

Test error cases:

```bash
# Test status without development.md
cd /tmp/test-speculate
rm docs/development.md
uv run --project /path/to/speculate/cli speculate status
echo "Exit code: $?"
# Should fail with exit code 1

# Test install without docs/
cd /tmp
mkdir test-empty && cd test-empty
uv run --project /path/to/speculate/cli speculate install
echo "Exit code: $?"
# Should fail with exit code 1

# Test update without .copier-answers.yml
uv run --project /path/to/speculate/cli speculate update
echo "Exit code: $?"
# Should fail with exit code 1
```

**Check:**

- [ ] Missing development.md shows red X and error message

- [ ] Missing docs/ shows helpful error message

- [ ] Missing .copier-answers.yml suggests running init first

- [ ] All error cases return exit code 1

#### 9. Cleanup

```bash
rm -rf /tmp/test-speculate /tmp/test-empty
```

## User Review Requested

Please perform the manual validation steps above and report:

1. Any issues with CLI output formatting or clarity

2. Any unexpected behavior or error messages

3. Any missing functionality compared to the plan spec

4. Any improvements or changes needed before Phase 5 (Publishing)
