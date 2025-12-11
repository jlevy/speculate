# Plan Spec: Install Command Improvements

## Purpose

This is a technical design doc for improving the `speculate install` command with better
symlink handling, merging of agent-rules from multiple sources, and safer default
behavior for existing files.

## Background

The current `speculate install` command sets up tool configurations (CLAUDE.md,
AGENTS.md, .cursor/rules/) for AI coding tools.
However, it has several limitations:

1. **No symlink handling**: If CLAUDE.md is symlinked to AGENTS.md (or vice versa), the
   command doesn’t detect this and may attempt to write to both, causing issues.

2. **Single source for agent-rules**: Currently only installs rules from
   `docs/general/agent-rules/`. Users may want project-specific rules in
   `docs/project/agent-rules/` that should be merged with general rules.

3. **Unsafe overwrites**: The command always overwrites existing `.cursor/rules/*.mdc`
   symlinks without checking if the user wants to preserve manual configurations.

See [plan-2025-12-02-speculate-cli.md](plan-2025-12-02-speculate-cli.md) for the
original CLI implementation spec.

## Summary of Task

Improve `speculate install` with three enhancements:

1. **Symlink detection**: Skip files that are symlinks (e.g., if CLAUDE.md -> AGENTS.md,
   only write to AGENTS.md)

2. **Merge agent-rules from multiple sources**: Install from both
   `docs/general/agent-rules/` and `docs/project/agent-rules/`, with project files
   taking precedence

3. **Safe defaults with --force flag**: Don’t overwrite or change existing
   files/symlinks unless `--force` is passed

## Backward Compatibility

### User-Facing Changes

| Area | Before | After | Migration |
| --- | --- | --- | --- |
| CLAUDE.md/AGENTS.md symlinks | May cause issues | Skipped cleanly | None required |
| Project-specific rules | Not supported | Merged with general rules | Create `docs/project/agent-rules/` if desired |
| Existing .cursor/rules | Always overwritten | Preserved unless --force | Pass --force to get old behavior |

### Breaking Changes

None. All changes are additive or improve safety.
Users who want the previous overwrite behavior can use `--force`.

## Stage 1: Planning Stage

### Requirements

**Must Have:**

- [ ] Detect and skip symlinked CLAUDE.md/AGENTS.md files (only write to the target, not
  the link)

- [ ] Collect agent-rules from both `docs/general/agent-rules/` and
  `docs/project/agent-rules/`

- [ ] Project rules take precedence (same-named file in project/ overrides general/)

- [ ] Add `--force` flag to `install` command (already exists in argparse, need to wire
  it up)

- [ ] Default behavior: skip existing `.cursor/rules/*.mdc` files unless `--force` is
  set

- [ ] Show clear output when files are skipped vs created vs updated

**Not In Scope:**

- Multiple project-specific rule directories

- Rule file merging (project file completely replaces general file of same name)

- Automatic detection of which rules to exclude

### Acceptance Criteria

1. Running `speculate install` when CLAUDE.md -> AGENTS.md skips CLAUDE.md and only
   updates AGENTS.md

2. Rules from `docs/project/agent-rules/` appear in `.cursor/rules/` alongside general
   rules

3. If both general and project have `python-rules.md`, project version is used

4. Running `speculate install` twice without `--force` doesn’t recreate symlinks
   (idempotent for cursor rules)

5. Running `speculate install --force` recreates all symlinks even if they exist

6. Clear messaging shows what was skipped, created, and overwritten

## Stage 2: Architecture Stage

### Current Implementation Analysis

From [cli/src/speculate/cli/cli_commands.py](cli/src/speculate/cli/cli_commands.py):

**`_ensure_speculate_header(path: Path)`** (lines 355-376):

- Already has idempotent behavior for CLAUDE.md/AGENTS.md

- Needs symlink check added at the start

**`_setup_cursor_rules(project_root, include, exclude)`** (lines 438-480):

- Currently only looks at `docs/general/agent-rules/`

- Always overwrites existing symlinks (line 469-470)

- Needs to merge from multiple directories

- Needs to respect `--force` flag

### Proposed Changes

#### 1. Symlink Detection Helper

```python
def _is_symlink(path: Path) -> bool:
    """Check if path is a symlink (doesn't follow the link)."""
    return path.is_symlink()

def _get_symlink_target(path: Path) -> Path | None:
    """Get the target of a symlink, or None if not a symlink."""
    if path.is_symlink():
        return path.resolve()
    return None
```

#### 2. Update `_ensure_speculate_header`

Add at the start of the function:
```python
# Skip symlinks - only write to the actual target
if path.is_symlink():
    target = path.resolve()
    print_info(f"{path.name} is a symlink to {target.name}, skipping")
    return
```

#### 3. Update `_setup_cursor_rules`

Refactor to:

1. Collect rules from both directories

2. Build a merged dict with project taking precedence

3. Only create symlinks for files that don’t exist (unless `--force`)

```python
def _setup_cursor_rules(
    project_root: Path,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    force: bool = False,
) -> None:
    # Collect rules from both sources
    general_rules = project_root / "docs" / "general" / "agent-rules"
    project_rules = project_root / "docs" / "project" / "agent-rules"

    # Build merged dict: stem -> full path (project takes precedence)
    rules: dict[str, Path] = {}
    if general_rules.exists():
        for f in general_rules.glob("*.md"):
            rules[f.stem] = f
    if project_rules.exists():
        for f in project_rules.glob("*.md"):
            rules[f.stem] = f  # Overwrites general if same name

    # Create symlinks
    for stem, rule_path in sorted(rules.items()):
        link_path = cursor_dir / (stem + ".mdc")

        if link_path.exists() or link_path.is_symlink():
            if not force:
                skipped_count += 1
                continue
            link_path.unlink()

        # Create relative symlink
        relative_target = _compute_relative_path(link_path, rule_path)
        link_path.symlink_to(relative_target)
```

#### 4. Update `install()` function signature

```python
def install(
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    force: bool = False,  # Add this parameter
) -> None:
```

#### 5. Update `cli_main.py` to pass `force` argument

The argparse already has `--force` for uninstall; add it to install as well.

### Files to Modify

| File | Changes |
| --- | --- |
| `cli/src/speculate/cli/cli_commands.py` | Update `_ensure_speculate_header`, `_setup_cursor_rules`, `install` |
| `cli/src/speculate/cli/cli_main.py` | Add `--force` argument to install subparser, pass to `install()` |
| `cli/tests/test_cli_commands.py` | Add tests for symlink handling, rule merging, force flag |

## Stage 3: Refine Architecture

### Reusable Components

- The symlink detection is simple Python stdlib (`Path.is_symlink()`)

- The pattern matching (`_matches_patterns`) already exists and can be reused

- The relative symlink creation pattern already exists in `_setup_cursor_rules`

### Simplifications

1. **Symlink detection**: Use `Path.is_symlink()` directly rather than creating a helper

2. **Rule merging**: Simple dict merge pattern (no complex logic needed)

3. **Force flag**: Boolean flag passed through the call chain

### Edge Cases to Handle

1. **Circular symlinks**: CLAUDE.md -> AGENTS.md -> CLAUDE.md (unlikely but should not
   crash)

2. **Broken symlinks**: Existing broken .mdc symlinks should be cleaned up

3. **Missing directories**: `docs/project/agent-rules/` may not exist (skip gracefully)

4. **Same file**: If CLAUDE.md and AGENTS.md are both symlinks to the same target, only
   update once

* * *

**Next Step:** Implementation in Phase 1 below.

## Stage 4: Implementation

### Phase 1: Symlink Handling and Force Flag

**Tasks:**

- [x] Update `_ensure_speculate_header` to skip symlinks

- [x] Add `force` parameter to `install()` and `_setup_cursor_rules()`

- [x] Update `_setup_cursor_rules` to skip existing files unless force=True

- [x] Add `--force` argument to install subparser in cli_main.py

- [x] Pass force argument through to install()

- [x] Create CLAUDE.md as symlink to AGENTS.md when CLAUDE.md doesn't exist

### Phase 2: Merge Agent Rules from Multiple Sources

**Tasks:**

- [x] Refactor `_setup_cursor_rules` to collect rules from both general and project
  directories

- [x] Build merged dict with project taking precedence

- [x] Compute relative symlink paths correctly for both sources

- [x] Handle missing project agent-rules directory gracefully

### Phase 3: Testing and Output

**Tasks:**

- [x] Add tests for symlink detection (CLAUDE.md symlinked to AGENTS.md)

- [x] Add tests for rule merging (project takes precedence)

- [x] Add tests for force flag behavior

- [x] Update output messages to show skipped/created/overwritten counts

- [x] Add tests for CLAUDE.md -> AGENTS.md symlink creation

## Stage 5: Validation

**Validation Checklist:**

- [ ] `speculate install` with CLAUDE.md -> AGENTS.md symlink skips CLAUDE.md

- [ ] Rules from `docs/project/agent-rules/` appear in `.cursor/rules/`

- [ ] Project rules override general rules of same name

- [ ] `speculate install` is idempotent without `--force`

- [ ] `speculate install --force` recreates all symlinks

- [ ] All existing tests pass

- [ ] New tests cover edge cases
