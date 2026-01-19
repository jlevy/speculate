# Implementation Spec: Speculate CLI

## Purpose

This is an implementation spec, used to track and record the implementation of the
Speculate CLI tool.

This should be filled in after the Plan Spec is written.
The Plan Spec covers Stages 1-2 (Planning, Architecture) and Stage 3 (Refine
Architecture). This Implementation Spec covers the actual implementation with phased
tasks.

It should be updated during the development process, then kept as a record for later
context once implementation is complete.

**Feature Plan:** [plan-2025-12-02-speculate-cli.md](plan-2025-12-02-speculate-cli.md)

## Stage 3: Implementation Stage

### Implementation Phases

The implementation is broken into phases that may be committed and tested separately:

- Phase 1: Project Setup — Rename package, add dependencies, create copier.yml

- Phase 2: CLI Structure — Create cli_main.py and cli_commands.py with stubs

- Phase 3: Command Implementations — Implement init, update, install, status commands

- Phase 3.5: Uninstall Command — Implement uninstall command with non-destructive
  removal

- Phase 4: Testing and Polish — Test all flows, lint, fix issues

- Phase 5: Publishing — GitHub Actions, PyPI, README

## Phase 1: Project Setup

### Files to Touch

- `cli/pyproject.toml` — Add dependencies, update entry point

- `cli/src/speculate/__init__.py` — Update package init

- `copier.yml` — Create new file at repo root

### Tasks

- [x] Add dependencies to `cli/pyproject.toml`:

  ```toml
  dependencies = [
      "copier>=9.4.0",
      "clideps>=0.1.8",
      "rich>=14.0.0",
      "pyyaml>=6.0",
      "strif>=3.0.1",
      "prettyfmt>=0.4.1",
  ]
  ```

- [x] Update entry point in `cli/pyproject.toml` (depends on Phase 2 cli/ module):

  ```toml
  [project.scripts]
  speculate = "speculate.cli.cli_main:main"
  ```

- [x] Create `copier.yml` at repo root:

  ```yaml
  _min_copier_version: "9.4.0"
  
  # Only copy docs/ directory using negation patterns (gitignore-style)
  # First exclude everything, then whitelist only root-level docs/
  # The leading / anchors the pattern to the template root
  _exclude:
    - "**"
    - "!/docs"
    - "!/docs/**"
  
  _message_after_copy: |
    Speculate docs installed!
    See docs/docs-overview.md for usage guide.
  ```

  **Note:** The original planned patterns (`"*"`, `".*"`, `"!docs/"`) did not work
  correctly with copier/pathspec.
  The working solution uses gitignore-style negation patterns with leading `/` to anchor
  to the template root, preventing `cli/docs/` from being inadvertently included.

### Automated Testing Strategy

- Run `uv sync` to verify dependencies install correctly

- Run `make lint` to verify no lint errors

### Libraries Used

| Library | Version | Purpose |
| --- | --- | --- |
| copier | >=9.4.0 | Template management and updates |
| clideps | >=0.1.8 | CLI utilities (ReadableColorFormatter) |
| rich | >=14.0.0 | Terminal output formatting |
| pyyaml | >=6.0 | Parse .copier-answers.yml |
| strif | >=3.0.1 | Atomic file operations ([docs](https://github.com/jlevy/strif)) |
| prettyfmt | >=0.4.1 | Human-friendly formatting ([docs](https://github.com/jlevy/prettyfmt)) |

### Open Questions (resolve now)

- [x] Keep existing `speculate` module or remove?
  → Remove, replace with speculate

### Out of Scope (do NOT do now)

- Actual command implementations (Phase 3)

- Publishing to PyPI (Phase 5)

## Phase 2: CLI Structure

### Files to Touch

- `cli/src/speculate/cli/__init__.py` — Create empty init

- `cli/src/speculate/cli/cli_main.py` — Main entry point with argparse

- `cli/src/speculate/cli/cli_commands.py` — Command function stubs

### Tasks

- [x] Create `cli/src/speculate/cli/` directory

- [x] Create `cli/src/speculate/cli/__init__.py` (empty file)

- [x] Create `cli/src/speculate/cli/cli_main.py` with full implementation from plan spec

- [x] Create `cli/src/speculate/cli/cli_commands.py` with full implementations:

  ```python
  from __future__ import annotations
  from rich import print as rprint
  
  def init(
      destination: str = ".",
      force: bool = False,
      template: str = "gh:jlevy/speculate"
  ) -> None:
      """Initialize docs in a project using Copier."""
      rprint("[yellow]Not implemented yet[/yellow]")
  
  def update() -> None:
      """Update docs from the upstream template."""
      rprint("[yellow]Not implemented yet[/yellow]")
  
  def install(include: list[str] | None = None, exclude: list[str] | None = None) -> None:
      """Generate tool configs for Cursor, Claude Code, and Codex."""
      rprint("[yellow]Not implemented yet[/yellow]")
  
  def status() -> None:
      """Show current template version and sync status."""
      rprint("[yellow]Not implemented yet[/yellow]")
  ```

- [x] Remove legacy `cli/src/speculate/speculate.py` and update `__init__.py`

- [x] Test `cd cli && uv run speculate --help` works

- [x] Test `cd cli && uv run speculate --version` works

### Automated Testing Strategy

- Run `uv run speculate --help` — should show usage

- Run `uv run speculate --version` — should show version

- Run `uv run speculate init --help` — should show init help

- Run `make lint` — should pass

### Libraries Used

No new libraries beyond Phase 1.

### Open Questions (resolve now)

None.

### Out of Scope (do NOT do now)

- Actual command logic (Phase 3)

- Copier integration (Phase 3)

## Phase 3: Command Implementations

### Files to Touch

- `cli/src/speculate/cli/cli_commands.py` — Full implementations

### Tasks

- [x] Implement `init` command:

  - Support `--template` argument (default: “gh:jlevy/speculate”)

  - Copy template using `copier.run_copy(template, dst)`

  - Copy `docs/project/development.sample.md` to `docs/development.md` if the
    destination `development.md` does not exist.

  - Automatically call `install()` after copy

  - Show instructions about customizing `docs/development.md`

- [x] Implement `update` command:

  - Check `.copier-answers.yml` exists

  - Run `copier.run_update(str(cwd), conflict="inline")`

  - Automatically call `install()` after update

- [x] Implement `install` command:

  - Create/update `.speculate/settings.yml` with:

    ```yaml
    last_update: "2024-12-03T12:00:00Z"
    last_cli_version: "0.1.0"
    last_docs_version: "v0.2.3" # from .copier-answers.yml
    ```

  - Support `--include` and `--exclude` patterns (wildcards: `*`, `**`)

  - For CLAUDE.md and AGENTS.md: Add speculate header if not present (idempotent)

  - Header format (two lines, matches repo’s own CLAUDE.md):

    ```
    IMPORTANT: You MUST read ./docs/development.md and ./docs/docs-overview.md for project documentation.
    (This project uses Speculate project structure.)
    ```

  - Check for “Speculate project structure” marker to avoid duplicate headers

  - Create `.cursor/rules/` symlinks with `.mdc` extension pointing to `.md` files

- [x] Implement `status` command:

  - Check `.speculate/settings.yml` and display last_update, last_cli_version

  - Check `.copier-answers.yml`, `docs/`, tool configs

  - **Error if `docs/development.md` is missing** (required setup)

  - Exit with code 1 if development.md missing

- [x] Implement helper functions:

  - `_update_speculate_settings(project_root)` — Create/update `.speculate/settings.yml`

  - `_ensure_speculate_header(path)` — Idempotent header management

  - `_matches_patterns(filename, include, exclude)` — Pattern matching with fnmatch

  - `_setup_cursor_rules(root, include, exclude)` — Symlink creation with `.mdc`
    extension

  - `_get_dir_stats(path)` — File count and size

### Automated Testing Strategy

- Create a temp directory and run `speculate init` — should create docs/

- Run `speculate status` — should show initialized state

- Run `speculate install` — should create .speculate/settings.yml, CLAUDE.md, AGENTS.md,
  .cursor/rules/

- Verify `.speculate/settings.yml` contains last_update, last_cli_version,
  last_docs_version

- Run `speculate status` again — should show all configs present including settings.yml
  info

- Run `make lint` — should pass

### Libraries Used

No new libraries beyond Phase 1.

### Open Questions (resolve now)

- [x] For symlinks, use relative paths?
  → Yes, `../../docs/general/agent-rules/`

### Out of Scope (do NOT do now)

- Custom template URLs

- Windsurf configuration

- Interactive questionnaire

## Phase 3.5: Uninstall Command

### Files to Touch

- `cli/src/speculate/cli/cli_commands.py` — Add uninstall command and helper functions

- `cli/src/speculate/cli/cli_main.py` — Add uninstall to command list and parser

- `cli/tests/test_cli_commands.py` — Add uninstall tests

### Tasks

- [x] Add `re` import to `cli_commands.py`

- [x] Add `SPECULATE_HEADER_PATTERN` regex constant:

  ```python
  SPECULATE_HEADER_PATTERN = re.compile(
      r"^IMPORTANT: You MUST read [^\n]*development\.md[^\n]*\n"
      r"\(This project uses Speculate project structure\.\)\n*",
      re.MULTILINE,
  )
  ```

- [x] Implement `_remove_speculate_header(path: Path)` helper:

  - Check if file exists and contains SPECULATE_MARKER

  - Use regex to remove header pattern

  - If file empty after removal, delete the file

  - Use cli_ui utilities for consistent logging

- [x] Implement `_remove_cursor_rules(project_root: Path)` helper:

  - Find all `.mdc` symlinks in `.cursor/rules/`

  - Remove symlinks that point to `docs/general/agent-rules/` or are broken

  - Log count of removed symlinks

- [x] Implement `uninstall(force: bool = False)` command:

  - Preview what will be removed (CLAUDE.md header, AGENTS.md header, symlinks,
    settings.yml)

  - Confirm with user unless `--force`

  - Call helper functions to remove each component

  - Log final summary

  - Print note that docs/ is preserved

- [x] Update `cli_main.py`:

  - Import `uninstall` from cli_commands

  - Add `uninstall` to `ALL_COMMANDS` list

  - Add `--force` argument for uninstall subparser

  - Add uninstall case in main() dispatch

- [x] Add unit tests for header operations (isolated tests on temp files):

  - `test_ensure_speculate_header_creates_new_file` — header added to non-existent file

  - `test_ensure_speculate_header_prepends_to_existing` — header prepended to file with
    content

  - `test_ensure_speculate_header_idempotent` — no change if header already present

  - `test_remove_speculate_header_preserves_content` — header removed, other content
    preserved

  - `test_remove_speculate_header_works_when_not_at_top` — header removed even when user
    added content above it (uses `re.MULTILINE` so `^` matches any line start)

  - `test_remove_speculate_header_deletes_empty_file` — file deleted if only header

  - `test_remove_speculate_header_no_op_if_no_marker` — file unchanged if no marker
    present

  - `test_remove_speculate_header_no_op_if_file_missing` — no error if file doesn’t
    exist

- [x] Add integration tests for uninstall command:

  - `test_uninstall_removes_header_from_claude_md`

  - `test_uninstall_removes_header_from_agents_md`

  - `test_uninstall_removes_cursor_symlinks`

  - `test_uninstall_removes_settings_yml`

  - `test_uninstall_preserves_copier_answers`

  - `test_uninstall_preserves_docs_directory`

  - `test_uninstall_with_force_skips_confirmation`

  - `test_uninstall_nothing_to_do` — when no speculate configs present

### Automated Testing Strategy

- Run `speculate install` then `speculate uninstall --force`

- Verify CLAUDE.md header removed but other content preserved

- Verify AGENTS.md header removed but other content preserved

- Verify .cursor/rules/ symlinks removed

- Verify .speculate/settings.yml removed

- Verify .speculate/copier-answers.yml preserved

- Verify docs/ directory preserved

- Run `make lint` — should pass

- Run `make test` — should pass

### Libraries Used

No new libraries beyond Phase 1 (uses `re` from stdlib).

### Open Questions (resolve now)

- [x] Should uninstall require confirmation?
  → Yes, unless `--force` is passed

- [x] Should uninstall remove .speculate/copier-answers.yml?
  → No, preserve it so user can still run `speculate update` later

- [x] Should uninstall remove docs/? → No, user should remove manually if desired

### Out of Scope (do NOT do now)

- `--dry-run` flag (preview only mode)

- Selective uninstall (e.g., only CLAUDE.md)

## Phase 4: Testing and Polish

### Files to Touch

- Various files for bug fixes and polish

### Tasks

- [x] Test `speculate init` in a fresh empty directory

- [x] Test `speculate init --template .` using the local repo as template

- [x] Test `speculate init` in a directory with existing docs/

- [ ] Test `speculate update` after making upstream changes (requires published
  template)

- [x] Test `speculate install` creates correct symlinks

- [ ] Test `speculate uninstall` removes tool configs correctly

- [ ] Test `speculate uninstall` preserves docs/ and copier-answers.yml

- [x] Test `speculate status` shows accurate information

- [x] Run `make lint` and fix any issues

- [x] Run `make test` and ensure tests pass (43 tests passing)

- [x] Verify all `--help` messages are clear

### Automated Testing Strategy

- [x] Full integration test in temp directory (test_integration.py)

- [x] Verify symlinks work correctly

- [x] Test error cases (missing .copier-answers.yml, missing docs/)

### Libraries Used

No new libraries.

### Open Questions (resolve now)

None.

### Out of Scope (do NOT do now)

- PyPI publishing (Phase 5)

## Phase 5: Publishing

### Files to Touch

- `.github/workflows/publish.yml` — PyPI publishing workflow

- `README.md` — Add Speculate usage documentation

### Tasks

- [ ] Verify `.github/workflows/publish.yml` exists and is configured

- [ ] Create a git tag for initial release (e.g., v0.1.0)

- [ ] Push tag to trigger PyPI publish

- [ ] Test `uvx speculate --version` works

- [ ] Test `uvx speculate init` in a fresh project

- [ ] Update README.md with:

  - Speculate description and purpose

  - Installation instructions (`uvx speculate` or `uv tool install speculate`)

  - Usage examples for all commands

  - Link to docs/docs-overview.md

### Automated Testing Strategy

- Test `uvx speculate` installs and runs correctly

- Test all commands work via uvx

### Libraries Used

No new libraries.

### Open Questions (resolve now)

- [x] Initial version number?
  → Confirmed: v0.1.0

### Out of Scope (do NOT do now)

- Documentation website

- Custom template support

- Windsurf configuration

## Bug Fixes

### Fix: .copier-answers.yml not being created (2025-12-02)

**Problem:** `speculate init` was not creating `.copier-answers.yml`, which is required
for `speculate update` to work.
The `status` command also showed a yellow ✘ for this missing file instead of a red
error.

**Root Cause:** Copier requires a template file named
`{{_copier_conf.answers_file}}.jinja` in the template root for it to create the answers
file. This file was missing.

**Fix:**

1. Created `{{_copier_conf.answers_file}}.jinja` at repo root with contents:
   ```
   # Changes here will be overwritten by Copier; do NOT edit by hand
   {{ _copier_answers|to_nice_yaml -}}
   ```

2. Updated `copier.yml` to use explicit exclusions instead of `**` negation patterns
   (the negation pattern approach was also excluding the answers file output)

3. Updated `status` command to use `print_error_item` for missing `.copier-answers.yml`
   and set `has_errors = True` so status exits with code 1

4. Added test `test_fails_without_copier_answers` to verify this behavior

**Files Changed:**

- `copier.yml` — Rewrote exclude patterns

- `{{_copier_conf.answers_file}}.jinja` — New file

- `cli/src/speculate/cli/cli_commands.py` — Updated status error handling

- `cli/tests/test_cli_commands.py` — Added new test, updated existing tests
