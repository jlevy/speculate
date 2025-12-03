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

- Phase 3: Command Implementations — Implement all four commands

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

- [x] Update entry point in `cli/pyproject.toml`:

  ```toml
  [project.scripts]
  speculate = "speculate.cli.cli_main:main"
  ```

- [ ] Create `copier.yml` at repo root:

  ```yaml
  _min_copier_version: "9.4.0"
  
  _exclude:
    - copier.yml
    - cli/
    - LICENSE
    - .git/
    - .github/
    - .cursor/
    - __pycache__/
    - "*.pyc"
    - "*.lock"
  
  _skip_if_exists:
    - docs/project/development.md
    - "docs/project/specs/active/*"
    - "docs/project/specs/done/*"
    - "docs/project/specs/future/*"
    - "docs/project/specs/paused/*"
    - "docs/project/architecture/current/*"
    - "docs/project/architecture/archive/*"
    - "docs/project/research/current/*"
    - "docs/project/research/archive/*"
  
  _message_after_copy: |
    Speculate docs installed!
    See docs/DOCS-README.md for usage guide.
  ```

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

- [ ] Create `cli/src/speculate/cli/` directory

- [ ] Create `cli/src/speculate/cli/__init__.py` (empty file)

- [ ] Create `cli/src/speculate/cli/cli_main.py` with full implementation from plan spec

- [ ] Create `cli/src/speculate/cli/cli_commands.py` with stub functions:

  ```python
  from __future__ import annotations
  from rich import print as rprint
  
  def init(destination: str = ".", force: bool = False) -> None:
      """Initialize docs in a project using Copier."""
      rprint("[yellow]Not implemented yet[/yellow]")
  
  def update() -> None:
      """Update docs from the upstream template."""
      rprint("[yellow]Not implemented yet[/yellow]")
  
  def install() -> None:
      """Generate tool configs for Cursor, Claude Code, and Codex."""
      rprint("[yellow]Not implemented yet[/yellow]")
  
  def status() -> None:
      """Show current template version and sync status."""
      rprint("[yellow]Not implemented yet[/yellow]")
  ```

- [ ] Test `cd cli && uv run speculate --help` works

- [ ] Test `cd cli && uv run speculate --version` works

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

- [ ] Implement `init` command:

  - Copy template using `copier.run_copy("gh:jlevy/speculate", dst)`

  - Automatically call `install()` after copy

  - Show instructions about creating `docs/project/development.md`

- [ ] Implement `update` command:

  - Check `.copier-answers.yml` exists

  - Run `copier.run_update(str(cwd), conflict="inline")`

  - Automatically call `install()` after update

- [ ] Implement `install` command:

  - Support `--include` and `--exclude` patterns (wildcards: `*`, `**`)

  - For CLAUDE.md and AGENTS.md: Add speculate header if not present (idempotent)

  - Header: `"IMPORTANT: You must read @docs/DOCS-README.md for project documentation
    (uses speculate project structure)."`

  - Check for “speculate project structure” to avoid duplicate headers

  - Create `.cursor/rules/` symlinks with `.mdc` extension pointing to `.md` files

- [ ] Implement `status` command:

  - Check `.copier-answers.yml`, `docs/`, tool configs

  - **Error if `docs/project/development.md` is missing** (required setup)

  - Exit with code 1 if development.md missing

- [ ] Implement helper functions:

  - `_ensure_speculate_header(path)` — Idempotent header management

  - `_matches_patterns(filename, include, exclude)` — Pattern matching with fnmatch

  - `_setup_cursor_rules(root, include, exclude)` — Symlink creation with `.mdc`
    extension

  - `_get_dir_stats(path)` — File count and size

### Automated Testing Strategy

- Create a temp directory and run `speculate init` — should create docs/

- Run `speculate status` — should show initialized state

- Run `speculate install` — should create CLAUDE.md, AGENTS.md, .cursor/rules/

- Run `speculate status` again — should show all configs present

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

## Phase 4: Testing and Polish

### Files to Touch

- Various files for bug fixes and polish

### Tasks

- [ ] Test `speculate init` in a fresh empty directory

- [ ] Test `speculate init` in a directory with existing docs/

- [ ] Test `speculate update` after making upstream changes

- [ ] Test `speculate install` creates correct symlinks

- [ ] Test `speculate status` shows accurate information

- [ ] Run `make lint` and fix any issues

- [ ] Run `make test` and ensure tests pass

- [ ] Verify all `--help` messages are clear

### Automated Testing Strategy

- Full integration test in temp directory

- Verify symlinks work correctly

- Test error cases (missing .copier-answers.yml, missing docs/)

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

  - Link to docs/DOCS-README.md

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
