# Plan Spec: Mirror Mode and Gradual Doc Customization

## Purpose

This spec defines how Speculate should support a mirror-based architecture with gradual
customization, allowing users to run Speculate with varying levels of git footprint—from
zero-footprint "mirror" mode to fully committed "full" mode—and incrementally adopt or
customize docs as needed.

## Background

Currently Speculate has no gitignore handling. All synced files (docs/, .speculate/, CLAUDE.md,
etc.) are visible to git and typically committed. This creates friction for:

1. Users who want to try Speculate without committing anything
2. Teams who want Speculate docs available locally but don't want to bloat git history
3. Users working on repos they don't own

This spec introduces a mode-based system with format versioning to support clean upgrades.

## Summary of Task

Implement three modes for controlling Speculate's git footprint:

| Mode | Description | Default for new installs |
|------|-------------|-------------------------|
| `mirror` | Zero git footprint—all files in `.speculate/mirror/` | Yes (recommended) |
| `project` | Hybrid—project docs tracked, general docs gitignored | No |
| `full` | Everything tracked in git (current behavior) | No |

Additionally:
- Introduce format versioning (`f0.1` → `f0.2`) with auto-upgrade
- Support custom upstream repos via `docs_repo` setting
- Add content state tracking for sync detection without git

## Backward Compatibility

- **Format**: f0.1 (current, implicit) → f0.2 (explicit, new features)
- **Auto-upgrade**: CLI will auto-upgrade f0.1 configs to f0.2 with logging
- **Fallback behavior**: Existing installs (no format field) treated as f0.1 `full` mode
- **Breaking changes**: None—existing behavior preserved unless user explicitly changes mode

---

## Stage 1: Planning Stage

### The Problem

Users have different needs for git integration:

1. **Trying Speculate**: Want zero footprint, easy cleanup
2. **Personal machines**: Want docs locally but not committed
3. **Team repos**: Want structure tracked but synced content gitignored
4. **Full adoption**: Want everything tracked for transparency

### The Mirror Architecture

The key insight is to use `.speculate/mirror/` as a staging area:

```
.speculate/                    # Can be fully gitignored in mirror mode
├── settings.yml               # Config including mode and format
├── copier-answers.yml         # Copier state
└── mirror/                    # Always gitignored internally
    └── docs/
        ├── general/           # Synced upstream content
        │   ├── agent-rules/
        │   ├── agent-shortcuts/
        │   └── ...
        └── project/           # Template structure (seeded once)
            └── specs/
```

**Key insight**: Copier always writes to `.speculate/mirror/docs/`, then a separate "publish"
step exposes content to `docs/` based on mode (via symlinks or copies).

### Mode Definitions

#### Mode: `mirror` (Zero Footprint, Default)

```
.speculate/              # Entirely gitignored (or just not committed)
├── mirror/docs/         # All docs live here
└── ...

docs -> .speculate/mirror/docs   # Symlink (gitignored)
CLAUDE.md                        # Generated (gitignored)
AGENTS.md                        # Generated (gitignored)
```

- Everything lives in `.speculate/mirror/`
- Top-level `docs/` is a symlink to the mirror
- Add `.speculate/` to `.gitignore` for true zero footprint
- Or just don't commit—user's choice

#### Mode: `project` (Hybrid)

```
.speculate/mirror/docs/general/    # Synced content (gitignored via .speculate/.gitignore)

docs/
├── general -> ../.speculate/mirror/docs/general  # Symlink (gitignored)
└── project/             # Real directory, tracked in git
    └── specs/           # User's project-specific docs
```

- Synced content in mirror, exposed via symlink
- Project-specific content (`docs/project/`) tracked normally
- `.gitignore` contains: `docs/general` (the symlink)

#### Mode: `full` (Everything Tracked)

```
docs/                    # Everything tracked in git
├── general/             # Synced
└── project/             # User content
```

- Current behavior—no mirror directory
- Copier writes directly to `docs/`
- Full git visibility

### What Gets Gitignored Per Mode

| Path | `mirror` | `project` | `full` |
|------|----------|-----------|--------|
| `.speculate/` | gitignored | tracked | tracked |
| `.speculate/mirror/` | n/a (inside .speculate) | gitignored | n/a |
| `docs/` (symlink in mirror mode) | gitignored | n/a | n/a |
| `docs/general/` (symlink in project mode) | n/a | gitignored | tracked |
| `docs/project/` | gitignored | tracked | tracked |
| `CLAUDE.md` | gitignored | tracked | tracked |
| `AGENTS.md` | gitignored | tracked | tracked |
| `.cursor/rules/` | gitignored | tracked | tracked |

### Not in Scope (v1)

- Remote sync status checking (can add later)
- Automatic `git add` operations (user controls their git)

---

## The Customize Command: Incremental Adoption

A key insight: users should be able to start with zero git footprint (mirror mode) and
**incrementally customize** parts they want to own locally. This creates a smooth adoption path:

1. **Try**: `speculate init` → everything mirrored, zero git footprint
2. **Adopt**: `speculate customize project` → project docs become local/tracked
3. **Extend**: `speculate customize general/agent-rules --tag python` → customize specific rules

### How Customize Works

The `customize` command copies files from `.speculate/mirror/` to `docs/` and updates the
publish configuration so those files are no longer symlinked from the mirror.

```bash
# Customize entire directory
speculate customize project
# Copies .speculate/mirror/docs/project/ → docs/project/
# docs/project/ is now a real directory, tracked in git

# Customize specific subdirectory
speculate customize general/agent-rules
# Copies .speculate/mirror/docs/general/agent-rules/ → docs/general/agent-rules/
# docs/general/agent-rules/ is now local; rest of general/ still mirrored

# Customize by tag (see Tag-Based Filtering below)
speculate customize --tag python
# Copies all files tagged with "python" from mirror to docs/
```

### Directory State After Customization

When you customize a path, that path becomes "owned" locally:

```
Before customize project:
  docs -> .speculate/mirror/docs  (symlink)

After customize project:
  docs/
  ├── general -> ../.speculate/mirror/docs/general  (symlink)
  └── project/                                       (real directory, local)
      └── specs/

After customize general/agent-rules:
  docs/
  ├── general/
  │   ├── agent-rules/                              (real directory, local)
  │   ├── agent-shortcuts -> ...                    (symlink)
  │   └── ...                                       (other symlinks)
  └── project/                                       (real directory)
```

### Customize Settings

Track what's customized in settings.yml:

```yaml
# .speculate/settings.yml
speculate:
  format: "f0.2"

mode: mirror
docs_repo: "gh:jlevy/speculate"

# Paths that have been customized (no longer mirrored)
customized:
  - "project"                    # Entire project/ directory
  - "general/agent-rules"        # Specific subdirectory
  # - "general/agent-rules/python-rules.md"  # Could also be individual files
```

### The Overlay Model

The key architectural insight is that `docs/` is an **overlay** on top of the mirror:

```
.speculate/mirror/docs/     ← Always contains FULL upstream content
         ↓
    [filters]               ← Controls what's visible
         ↓
    [customized paths]      ← Local overrides
         ↓
docs/                       ← Final merged view (symlinks + local files)
```

**Mirror is always full**: `speculate update` always syncs the complete upstream content
to `.speculate/mirror/docs/`. This ensures you can always "uncustomize" back to upstream.

**Filters control visibility**: The `filters` setting controls which files from the mirror
are exposed to `docs/`. Files not matching filters are simply not symlinked.

**Customizations override**: Customized paths are local copies that take precedence over
the mirror. The mirror version still exists (for diffing, reverting).

### Uncustomize: Reverting to Mirror

Users can drop customizations and revert to using the mirror version:

```bash
# Revert a customized path to use mirror again
speculate uncustomize project

# Revert specific files
speculate uncustomize general/agent-rules/python-rules.md

# Revert everything (back to pure mirror mode)
speculate uncustomize --all

# Preview what would be reverted (dry-run)
speculate uncustomize project --dry-run
# Output:
#   Would remove: docs/project/ (5 files, 12KB)
#   Would restore: symlink to .speculate/mirror/docs/project/
#   Changes in your version vs mirror:
#     - docs/project/specs/my-spec.md (local only, would be LOST)
#     - docs/project/development.md (modified, would revert to upstream)
```

**Safety**: `uncustomize` warns about local-only files and modifications before deleting.

### Diff Between Local and Mirror

Since the mirror always has the full upstream content:

```bash
# See what's different in your customized files vs upstream
speculate diff

# Diff specific path
speculate diff project

# Show which files are local-only (not in upstream)
speculate diff --local-only
```

### Mode Shortcuts

The modes are actually shortcuts for common customization patterns:

| Mode | Equivalent to |
|------|--------------|
| `mirror` | `speculate init` (nothing customized) |
| `project` | `speculate init && speculate customize project` |
| `full` | `speculate init && speculate customize project && speculate customize general` |

So `speculate init --mode project` is sugar for starting in mirror mode with `project/`
pre-customized.

---

## Copier Filtering Capabilities (Research)

Understanding Copier's native filtering is critical to this design. This section documents
what Copier can and cannot do, informing our architectural decisions.

### What Copier Supports

Copier provides **filename/path-based filtering only**:

1. **`_exclude` patterns** (gitignore-style):
   ```yaml
   _exclude:
     - "*.pyc"
     - "__pycache__"
     - "docs/internal/**"
   ```

2. **Conditional filenames via Jinja**:
   ```
   {% if use_python %}.python-version{% endif %}.jinja
   {% if ci == 'github' %}.github{% endif %}/workflows/
   ```

3. **Conditional directories**:
   ```
   template/{% if feature_a %}feature_a_dir{% endif %}/
   ```

4. **User answers controlling generation**: Questions with `when` conditions can skip
   entire template sections based on user input at copy time.

### What Copier Does NOT Support

- **Content-based filtering**: Cannot filter based on file contents (e.g., YAML frontmatter)
- **Runtime tag filtering**: No way to say "only copy files tagged with 'python'"
- **Dynamic include/exclude based on metadata**: Patterns must be known at template design time

### Sources

- [Copier Configuration Reference](https://copier.readthedocs.io/en/stable/configuring/)
- [Copier Template Reference](https://copier.readthedocs.io/en/latest/reference/template/)
- [Copier Negative Exclude Patterns Issue #1794](https://github.com/copier-org/copier/issues/1794)
- [Multiple Templates Discussion #855](https://github.com/orgs/copier-org/discussions/855)

### Architectural Decision: Post-Copier Filtering

Given Copier's limitations, we have two options for implementing tag-based filtering:

**Option A: Post-Copier Filtering (Chosen)**
```
Copier syncs everything → .speculate/mirror/
Speculate filters by tags → docs/ (symlinks only matching files)
```

- Copier always syncs full upstream content to mirror
- Speculate's overlay layer handles tag filtering via symlinks
- Clean separation of concerns
- Users can always `uncustomize` back to any file (mirror has everything)

**Option B: Pre-Copier Filtering (Rejected)**
```
Speculate reads upstream tags → generates dynamic _exclude list
Copier syncs only filtered content
```

- Would require fetching and parsing all upstream files before Copier runs
- Tight coupling between Speculate and Copier internals
- Lost content can't be recovered without re-running with different filters
- More complex error handling

**Decision**: Option A is cleaner and more robust. The mirror serves as a complete cache
of upstream content, and filtering happens at the Speculate layer when creating symlinks
or responding to `customize` commands. This also enables the `diff` command (compare local
vs upstream) since the mirror always has the full upstream state.

---

## Tag-Based Filtering

### Frontmatter Tags

Add optional YAML frontmatter to docs with tags:

```markdown
---
tags:
  - python
  - testing
  - tdd
---

# Python Testing Guidelines

...content...
```

### Tag Categories

Suggested tag taxonomy:

| Category | Example Tags |
|----------|-------------|
| Language | `python`, `typescript`, `go`, `rust` |
| Framework | `react`, `convex`, `fastapi`, `django` |
| Domain | `testing`, `ci-cd`, `documentation`, `security` |
| Tool | `cursor`, `claude`, `copilot` |

### Using Tags with Customize

```bash
# Customize all Python-related docs
speculate customize --tag python

# Customize multiple tags (OR logic)
speculate customize --tag python --tag testing

# Customize by glob AND tag
speculate customize general/agent-rules --tag python
# Only copies python-tagged files from general/agent-rules/

# List available tags
speculate tags
# Output:
#   python (5 files)
#   typescript (8 files)
#   testing (3 files)
#   ...
```

### Tag Implementation

```python
def get_file_tags(file_path: Path) -> set[str]:
    """Extract tags from YAML frontmatter."""
    content = file_path.read_text()
    if not content.startswith("---"):
        return set()

    # Parse frontmatter
    try:
        _, frontmatter, _ = content.split("---", 2)
        metadata = yaml.safe_load(frontmatter)
        return set(metadata.get("tags", []))
    except (ValueError, yaml.YAMLError):
        return set()

def filter_by_tags(
    files: list[Path],
    include_tags: set[str] | None = None,
    exclude_tags: set[str] | None = None,
) -> list[Path]:
    """Filter files by their frontmatter tags."""
    result = []
    for file in files:
        file_tags = get_file_tags(file)

        # Include if any include_tag matches (OR logic)
        if include_tags and not (file_tags & include_tags):
            continue

        # Exclude if any exclude_tag matches
        if exclude_tags and (file_tags & exclude_tags):
            continue

        result.append(file)
    return result
```

### Settings for Tag Filters

Persist tag filters in settings for future updates:

```yaml
# .speculate/settings.yml
speculate:
  format: "f0.2"

mode: mirror

# Tag-based filtering for what gets synced/installed
filters:
  include_tags:
    - python
    - testing
  exclude_tags:
    - convex  # Not using Convex in this project
```

When `speculate update` runs, it respects these filters:
- Only syncs files matching `include_tags` (if set)
- Excludes files matching `exclude_tags`
- Customized paths are never overwritten by sync

---

## Stage 2: Architecture Stage

### Format Versioning

Introduce explicit format versioning in `settings.yml`:

```yaml
# .speculate/settings.yml (f0.2 format)
speculate:
  format: "f0.2"

mode: mirror           # mirror | project | full
docs_repo: "gh:jlevy/speculate"  # Customizable upstream

# Install metadata (existing)
last_update: 2026-01-16T12:34:56+00:00
last_cli_version: 0.2.20
last_docs_version: abc123

# Content state for sync detection (new, only used in mirror/project modes)
content_state:
  docs/general/agent-rules/coding-style.md: "sha256:abc..."
  docs/general/agent-rules/testing.md: "sha256:def..."
```

### Format Detection Function

```python
def read_speculate_format(settings_path: Path) -> str:
    """Detect the format version of a settings file.

    Returns:
        "f0.1" - Legacy format (no speculate.format field)
        "f0.2" - Current format with explicit versioning
        Future versions as needed
    """
    if not settings_path.exists():
        return "f0.2"  # New installs get latest

    settings = _load_yaml(settings_path)
    speculate_section = settings.get("speculate", {})
    return speculate_section.get("format", "f0.1")
```

### Format Upgrade Strategy

```python
def maybe_upgrade_format(settings_path: Path) -> bool:
    """Upgrade settings to latest format if needed.

    Returns True if an upgrade was performed.
    """
    current = read_speculate_format(settings_path)
    latest = "f0.2"  # CLI's supported format

    if current == latest:
        return False

    if current == "f0.1":
        _upgrade_f01_to_f02(settings_path)
        print_info(f"Upgraded settings format: {current} → {latest}")
        return True

    return False

def _upgrade_f01_to_f02(settings_path: Path) -> None:
    """Upgrade f0.1 settings to f0.2 format."""
    settings = _load_yaml(settings_path)

    # Add speculate section with format
    settings["speculate"] = {"format": "f0.2"}

    # Existing installs default to 'full' mode (preserve behavior)
    if "mode" not in settings:
        settings["mode"] = "full"

    # Add default docs_repo
    if "docs_repo" not in settings:
        settings["docs_repo"] = "gh:jlevy/speculate"

    _write_yaml(settings_path, settings)
```

### The `docs_repo` Setting

Allow users to point to a fork of Speculate for customized docs:

```yaml
# .speculate/settings.yml
docs_repo: "gh:myorg/speculate-fork"  # Or full git URL
```

**Usage in copier operations:**

```python
def get_template_source(settings: dict) -> str:
    """Get the template source from settings or default."""
    return settings.get("docs_repo", "gh:jlevy/speculate")
```

**Documentation addition** (for docs-overview.md or similar):

> ### Customizing Speculate
>
> To customize the docs synced by Speculate, fork the repository and point your
> installation to your fork:
>
> ```bash
> # During init
> speculate init --docs-repo gh:myorg/speculate-fork
>
> # Or update existing config
> speculate config --docs-repo gh:myorg/speculate-fork
> ```
>
> Your fork should maintain the same directory structure (`docs/general/`, etc.)
> for compatibility. The `docs_repo` setting uses the same format as Copier
> templates (`gh:owner/repo` or a full git URL).

### CLI Command Updates

#### `speculate init`

```bash
# New flags
speculate init --mode mirror        # Zero footprint (default)
speculate init --mode project       # Hybrid mode
speculate init --mode full          # Everything tracked
speculate init --docs-repo gh:myorg/fork  # Custom upstream
```

#### `speculate config` (New Command)

```bash
# View current config
speculate config

# Change mode (restructures files)
speculate config --mode project

# Change upstream repo
speculate config --docs-repo gh:myorg/fork
```

#### `speculate status`

Enhanced output for mode awareness:

```
Speculate Status
  Template version: v0.2.20
  Source: gh:jlevy/speculate
  Last install: 2026-01-16T12:34:56 (CLI 0.2.20)
  Mode: mirror (docs/ gitignored)
  Format: f0.2

  docs/ exists (symlink → .speculate/mirror/docs)
  docs/development.md exists
  CLAUDE.md exists
  AGENTS.md exists
  .cursor/rules/ exists
```

### Gitignore Management

```python
GITIGNORE_MARKER_START = "### BEGIN SPECULATE ###"
GITIGNORE_MARKER_END = "### END SPECULATE ###"

GITIGNORE_ENTRIES = {
    "mirror": [
        "# Speculate (mirror mode - zero git footprint)",
        ".speculate/",
        "docs",  # The symlink
        "CLAUDE.md",
        "AGENTS.md",
        ".cursor/rules/",
    ],
    "project": [
        "# Speculate (project mode - synced docs gitignored)",
        "docs/general",  # The symlink
    ],
    "full": [
        # No entries - everything tracked
    ],
}

def update_gitignore_for_mode(mode: str, gitignore_path: Path) -> None:
    """Update .gitignore with appropriate Speculate entries.

    Uses markers to identify and update only our section.
    """
    entries = GITIGNORE_ENTRIES.get(mode, [])

    if gitignore_path.exists():
        content = gitignore_path.read_text()
        # Remove existing speculate section
        content = re.sub(
            f"{GITIGNORE_MARKER_START}.*?{GITIGNORE_MARKER_END}\n?",
            "",
            content,
            flags=re.DOTALL
        )
    else:
        content = ""

    if entries:
        section = f"{GITIGNORE_MARKER_START}\n"
        section += "\n".join(entries)
        section += f"\n{GITIGNORE_MARKER_END}\n"
        content = content.rstrip() + "\n\n" + section

    gitignore_path.write_text(content)
```

### Content State Tracking

For detecting local modifications when files are gitignored:

```python
def compute_content_state(docs_path: Path) -> dict[str, str]:
    """Hash all synced files for state comparison."""
    state = {}
    for file in docs_path.rglob("*.md"):
        rel_path = str(file.relative_to(docs_path.parent))
        content_hash = hashlib.sha256(file.read_bytes()).hexdigest()[:16]
        state[rel_path] = f"sha256:{content_hash}"
    return state

def detect_local_modifications(
    current_state: dict[str, str],
    saved_state: dict[str, str]
) -> list[str]:
    """Find files that changed since last sync."""
    modified = []
    for path, current_hash in current_state.items():
        if saved_state.get(path) != current_hash:
            modified.append(path)
    return modified
```

### Symlink Creation

```python
def publish_from_mirror(mode: str, project_root: Path) -> None:
    """Expose mirror content to docs/ based on mode."""
    mirror = project_root / ".speculate" / "mirror" / "docs"
    docs = project_root / "docs"

    if mode == "mirror":
        # Symlink entire docs/ to mirror
        if docs.exists() and not docs.is_symlink():
            shutil.rmtree(docs)
        if not docs.exists():
            docs.symlink_to(Path(".speculate/mirror/docs"))

    elif mode == "project":
        # Symlink general/, keep project/ as real directory
        docs.mkdir(exist_ok=True)
        general_link = docs / "general"
        if not general_link.exists():
            general_link.symlink_to(Path("../.speculate/mirror/docs/general"))

        # Copy project/ structure (don't overwrite existing)
        project_src = mirror / "project"
        project_dst = docs / "project"
        if project_src.exists() and not project_dst.exists():
            shutil.copytree(project_src, project_dst)

    elif mode == "full":
        # No symlinks - copier writes directly to docs/
        pass
```

---

## Stage 3: Implementation Plan

### Phase 1: Format Versioning Infrastructure

- [ ] Add `read_speculate_format()` function
- [ ] Add `maybe_upgrade_format()` with f0.1 → f0.2 upgrade
- [ ] Update `_update_speculate_settings()` to write f0.2 format
- [ ] Add unit tests for format detection and upgrade

### Phase 2: Mirror Architecture (Core)

- [ ] Create `.speculate/mirror/` directory structure
- [ ] Modify copier integration to always write to mirror
- [ ] Implement overlay resolution (mirror + customizations → docs/)
- [ ] Implement symlink creation for non-customized paths
- [ ] Update `install` to handle symlink-based docs

### Phase 3: Mode Configuration

- [ ] Add `mode`, `docs_repo`, `customized`, `filters` to settings schema
- [ ] Add `--mode` and `--docs-repo` flags to `init` command
- [ ] Create `config` command for viewing/changing settings
- [ ] Add unit tests for mode configuration

### Phase 4: Customize/Uncustomize Commands

- [ ] Implement `speculate customize <path>` command
  - [ ] Copy from mirror to docs/
  - [ ] Update `customized` list in settings
  - [ ] Recreate symlinks for remaining paths
- [ ] Implement `speculate uncustomize <path>` command
  - [ ] Detect local-only files and modifications
  - [ ] Warn user about data loss
  - [ ] Remove local copy, restore symlink
- [ ] Implement `speculate diff` command
  - [ ] Compare customized files vs mirror
  - [ ] Show local-only files
- [ ] Add unit tests for customize/uncustomize

### Phase 5: Tag-Based Filtering

- [ ] Implement `get_file_tags()` for frontmatter parsing
- [ ] Implement `filter_by_tags()` for file filtering
- [ ] Add `--tag` flag to `customize` command
- [ ] Implement `speculate tags` command to list available tags
- [ ] Persist tag filters in settings
- [ ] Apply filters during `update` and overlay resolution
- [ ] Add unit tests for tag parsing and filtering

### Phase 6: Gitignore Management

- [ ] Implement `update_gitignore_for_mode()`
- [ ] Integrate with `init`, `config`, and `customize` commands
- [ ] Add marker-based section management
- [ ] Add unit tests for gitignore manipulation

### Phase 7: Content State Tracking

- [ ] Implement `compute_content_state()`
- [ ] Store state in settings.yml after sync
- [ ] Implement `detect_local_modifications()`
- [ ] Integrate with `status` command

### Phase 8: Documentation & Testing

- [ ] Update docs-overview.md with mode documentation
- [ ] Add customization section for `docs_repo`
- [ ] Document the overlay model and customize workflow
- [ ] Add tags to existing docs files (python, typescript, etc.)
- [ ] Integration tests for each mode
- [ ] Migration testing from f0.1 to f0.2

---

## Stage 4: Validation Stage

### Unit Test Strategy for Format Upgrades

```python
# tests/test_format_upgrade.py

def test_read_format_missing_file():
    """New installs get latest format."""
    with tempfile.TemporaryDirectory() as tmp:
        settings_path = Path(tmp) / ".speculate" / "settings.yml"
        assert read_speculate_format(settings_path) == "f0.2"

def test_read_format_f01_implicit():
    """Legacy files without format field are f0.1."""
    with tempfile.TemporaryDirectory() as tmp:
        settings_path = Path(tmp) / "settings.yml"
        settings_path.write_text(yaml.dump({
            "last_update": "2025-01-01T00:00:00",
            "last_cli_version": "0.2.19",
        }))
        assert read_speculate_format(settings_path) == "f0.1"

def test_read_format_f02_explicit():
    """Files with format field return that version."""
    with tempfile.TemporaryDirectory() as tmp:
        settings_path = Path(tmp) / "settings.yml"
        settings_path.write_text(yaml.dump({
            "speculate": {"format": "f0.2"},
            "mode": "mirror",
        }))
        assert read_speculate_format(settings_path) == "f0.2"

def test_upgrade_f01_to_f02():
    """Upgrade adds format, mode, and docs_repo."""
    with tempfile.TemporaryDirectory() as tmp:
        settings_path = Path(tmp) / "settings.yml"
        settings_path.write_text(yaml.dump({
            "last_update": "2025-01-01T00:00:00",
            "last_cli_version": "0.2.19",
        }))

        upgraded = maybe_upgrade_format(settings_path)
        assert upgraded is True

        settings = _load_yaml(settings_path)
        assert settings["speculate"]["format"] == "f0.2"
        assert settings["mode"] == "full"  # Preserve existing behavior
        assert settings["docs_repo"] == "gh:jlevy/speculate"

def test_upgrade_preserves_existing_settings():
    """Upgrade doesn't overwrite existing values."""
    with tempfile.TemporaryDirectory() as tmp:
        settings_path = Path(tmp) / "settings.yml"
        settings_path.write_text(yaml.dump({
            "last_update": "2025-01-01T00:00:00",
            "last_cli_version": "0.2.19",
            "custom_field": "preserved",
        }))

        maybe_upgrade_format(settings_path)

        settings = _load_yaml(settings_path)
        assert settings["custom_field"] == "preserved"

def test_no_upgrade_when_current():
    """No upgrade when already at latest format."""
    with tempfile.TemporaryDirectory() as tmp:
        settings_path = Path(tmp) / "settings.yml"
        settings_path.write_text(yaml.dump({
            "speculate": {"format": "f0.2"},
            "mode": "mirror",
        }))

        upgraded = maybe_upgrade_format(settings_path)
        assert upgraded is False
```

### Integration Test Strategy

```python
def test_init_mirror_mode():
    """Mirror mode creates proper structure."""
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        init(mode="mirror")

        # Check structure
        assert (Path(tmp) / ".speculate" / "mirror" / "docs").is_dir()
        assert (Path(tmp) / "docs").is_symlink()
        assert (Path(tmp) / ".gitignore").exists()

        # Check gitignore
        gitignore = (Path(tmp) / ".gitignore").read_text()
        assert ".speculate/" in gitignore
        assert "docs" in gitignore

def test_init_project_mode():
    """Project mode creates hybrid structure."""
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        init(mode="project")

        # Check structure
        assert (Path(tmp) / "docs" / "general").is_symlink()
        assert (Path(tmp) / "docs" / "project").is_dir()
        assert not (Path(tmp) / "docs" / "project").is_symlink()

        # Check gitignore
        gitignore = (Path(tmp) / ".gitignore").read_text()
        assert "docs/general" in gitignore
        assert ".speculate/" not in gitignore  # .speculate tracked

def test_mode_switch():
    """Switching modes restructures files correctly."""
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        init(mode="full")

        # Switch to mirror
        config(mode="mirror")

        assert (Path(tmp) / "docs").is_symlink()
        assert (Path(tmp) / ".speculate" / "mirror" / "docs").is_dir()
```

---

## Open Questions

1. **Symlink compatibility**: Some Windows environments or tools don't handle symlinks well.
   Should we offer a copy-based alternative to symlinks?
   - Possible: `speculate config --symlink-mode copy` to use copies instead

2. **Copier's dirty check**: Copier may warn about dirty working directory in gitignored modes.
   Options:
   - Use `--trust` flag (if available)
   - Stash/unstash around copier operations
   - Accept messier output in gitignored modes

3. **Agent config files**: Should `.cursor/rules/` follow the same mode logic, or always be
   handled the same way regardless of mode?
   - Current thinking: Always symlinked to whichever version of the rule is active (mirror or local)

4. **Default mode for new users**: The spec proposes `mirror` as default. Confirm this is the
   right choice vs. `full` for maximum discoverability.
   - Pro mirror: Zero risk, easy cleanup, progressive adoption
   - Pro full: More obvious what Speculate does, easier to understand

5. **Tag inheritance**: Should tags apply to directories, or only individual files?
   - If a directory has a tag, do all files inherit it?
   - Or require explicit tagging on each file?

6. **Filter behavior on update**: When filters change, what happens to existing content?
   - Option A: Newly excluded files are removed from mirror
   - Option B: Newly excluded files remain but aren't symlinked
   - Leaning toward B for safety

7. **Conflict handling for customized files**: When upstream updates a file you've customized:
   - Currently: Your version is preserved, upstream in mirror (use `diff` to see)
   - Should we notify the user automatically?
   - Add a `speculate status --check-upstream` command?

---

## Appendix: User Workflows

### Workflow: Try Speculate without committing

```bash
$ cd my-project
$ speculate init   # Uses mirror mode by default

# Everything in .speculate/, nothing in git
$ git status
On branch main
nothing to commit, working tree clean

# When done experimenting
$ rm -rf .speculate docs CLAUDE.md AGENTS.md .cursor
```

### Workflow: Team adopts Speculate with minimal git noise

```bash
$ speculate init --mode project

# Only project structure committed
$ git status
new file: .speculate/settings.yml
new file: .speculate/copier-answers.yml
new file: docs/project/specs/.gitkeep
new file: docs/development.md
modified: .gitignore

# Future updates don't create new commits
$ speculate update
# Only .speculate/mirror/ changes (gitignored)
```

### Workflow: Fork and customize Speculate

```bash
# Fork gh:jlevy/speculate to gh:myorg/speculate-custom
# Make customizations to your fork

$ speculate init --docs-repo gh:myorg/speculate-custom
# Uses your fork for all synced content

# Or update existing installation
$ speculate config --docs-repo gh:myorg/speculate-custom
$ speculate update   # Pulls from your fork
```

### Workflow: Incremental Adoption (The Golden Path)

This is the recommended workflow for most users:

```bash
# Day 1: Try Speculate with zero commitment
$ cd my-project
$ speculate init
# Mirror mode (default): everything in .speculate/, nothing in git
# Agents can see all docs via symlinked docs/

$ git status
On branch main
nothing to commit, working tree clean  # Zero git footprint!

# Day 2: Start tracking project structure
$ speculate customize project
# docs/project/ is now a real directory, tracked in git
# You can add your own specs, architecture docs

$ git status
new file: docs/project/specs/.gitkeep
new file: docs/development.md
modified: .gitignore

$ git add -A && git commit -m "Add Speculate project structure"

# Day 3: Customize some rules for your stack
$ speculate tags
python (5 files)
typescript (8 files)
testing (3 files)
...

$ speculate customize --tag python
# All Python-related docs copied to local docs/

$ git add docs/general/agent-rules/python-*.md
$ git commit -m "Customize Python agent rules"

# Later: Pull updates, preserving your customizations
$ speculate update
# Mirror updated with latest upstream
# Your customized files unchanged
# New files from upstream auto-symlinked

# Decide: Upstream changed python-rules.md, want to see diff?
$ speculate diff general/agent-rules/python-rules.md
# Shows your version vs upstream

# Option A: Keep your version (do nothing)
# Option B: Merge manually, or:
$ speculate uncustomize general/agent-rules/python-rules.md
# Reverts to upstream version (warns if you have changes)
```

### Workflow: Filter by Technology Stack

```bash
# Python/FastAPI project - only want relevant docs
$ speculate init

# Set up filters (persisted in settings)
$ speculate config --include-tag python --include-tag testing
$ speculate config --exclude-tag typescript --exclude-tag react

# Now customize with filtered content
$ speculate customize general
# Only copies python/testing related docs, excludes typescript/react

# Future updates respect filters
$ speculate update
# Only syncs filtered content to mirror
```

---

## Appendix: Tagging Existing Docs

This section maps out the work needed to add consistent YAML frontmatter tags to all
existing Speculate docs.

### Frontmatter Schema

All docs should have consistent YAML frontmatter defined by a Pydantic model:

```python
from pydantic import BaseModel, Field
from datetime import date
from typing import Literal


class Author(BaseModel):
    """Author attribution, similar to git commit author."""
    name: str
    email: str | None = None


class DocMetadata(BaseModel):
    """YAML frontmatter schema for Speculate docs.

    This model defines the structure of frontmatter at the top of each
    markdown file, between --- delimiters.
    """

    # Content classification
    tags: list[str] = Field(
        default_factory=list,
        description="Content tags for filtering (e.g., python, testing, cli)"
    )

    # Authorship (like git commits)
    author: Author | None = Field(
        default=None,
        description="Original author of this document"
    )
    contributors: list[Author] = Field(
        default_factory=list,
        description="Additional contributors who have significantly edited"
    )

    # Lifecycle
    created: date | None = Field(
        default=None,
        description="Date document was created (YYYY-MM-DD)"
    )
    updated: date | None = Field(
        default=None,
        description="Date of last significant update"
    )

    # Status (optional, mainly for specs)
    status: Literal["draft", "active", "deprecated", "archived"] | None = Field(
        default=None,
        description="Document lifecycle status"
    )

    # For research docs
    sources: list[str] = Field(
        default_factory=list,
        description="URLs or references used in research docs"
    )
```

### Example Frontmatter

```yaml
---
tags:
  - python
  - testing
  - tdd
author:
  name: Jane Developer
  email: jane@example.com
contributors:
  - name: Claude
created: 2026-01-15
updated: 2026-01-16
---

# Python Testing Guidelines

...content...
```

### Minimal Frontmatter (Just Tags)

For simple docs, only tags are required:

```yaml
---
tags:
  - typescript
  - cli
---
```

### Proposed Tag Assignments

#### Agent Rules (`docs/general/agent-rules/`)

| File | Proposed Tags |
|------|---------------|
| `python-rules.md` | `python` |
| `python-rules-opinionated.md` | `python`, `opinionated` |
| `typescript-rules.md` | `typescript` |
| `typescript-cli-tool-rules.md` | `typescript`, `cli` |
| `convex-rules.md` | `typescript`, `convex` |
| `general-coding-rules.md` | `general` |
| `general-comment-rules.md` | `general` |
| `general-style-rules.md` | `general` |
| `general-testing-rules.md` | `general`, `testing` |
| `general-eng-assistant-rules.md` | `general` |
| `backward-compatibility-rules.md` | `general` |
| `tool-development-rules.md` | `general`, `cli` |
| `automatic-shortcut-triggers.md` | `general`, `workflow` |

#### Agent Guidelines (`docs/general/agent-guidelines/`)

| File | Proposed Tags |
|------|---------------|
| `general-tdd-guidelines.md` | `general`, `testing`, `tdd` |
| `golden-testing-guidelines.md` | `general`, `testing`, `golden-testing` |
| `typescript-testing-guidelines.md` | `typescript`, `testing` |
| `typescript-dependency-injection-guidelines.md` | `typescript`, `testing`, `di` |

#### Agent Shortcuts (`docs/general/agent-shortcuts/`)

| File | Proposed Tags |
|------|---------------|
| `shortcut-commit-code.md` | `general`, `workflow`, `git` |
| `shortcut-merge-upstream.md` | `general`, `workflow`, `git` |
| `shortcut-precommit-process.md` | `general`, `workflow` |
| `shortcut-create-pr-simple.md` | `general`, `workflow`, `git` |
| `shortcut-create-or-update-pr-with-validation-plan.md` | `general`, `workflow`, `git` |
| `shortcut-create-or-update-validation-plan.md` | `general`, `workflow` |
| `shortcut-review-pr.md` | `general`, `workflow`, `git` |
| `shortcut-review-pr-and-fix-with-beads.md` | `general`, `workflow`, `beads` |
| `shortcut-new-plan-spec.md` | `general`, `workflow`, `specs` |
| `shortcut-new-implementation-spec.md` | `general`, `workflow`, `specs` |
| `shortcut-new-validation-spec.md` | `general`, `workflow`, `specs` |
| `shortcut-implement-spec.md` | `general`, `workflow`, `specs` |
| `shortcut-refine-spec.md` | `general`, `workflow`, `specs` |
| `shortcut-update-spec.md` | `general`, `workflow`, `specs` |
| `shortcut-update-specs-status.md` | `general`, `workflow`, `specs` |
| `shortcut-new-architecture-doc.md` | `general`, `workflow`, `architecture` |
| `shortcut-revise-architecture-doc.md` | `general`, `workflow`, `architecture` |
| `shortcut-new-research-brief.md` | `general`, `workflow`, `research` |
| `shortcut-coding-spike.md` | `general`, `workflow` |
| `shortcut-implement-beads.md` | `general`, `workflow`, `beads` |
| `shortcut-new-implementation-beads-from-spec.md` | `general`, `workflow`, `beads` |
| `shortcut-cleanup-all.md` | `general`, `workflow`, `cleanup` |
| `shortcut-cleanup-update-docstrings.md` | `general`, `workflow`, `cleanup` |
| `shortcut-cleanup-remove-trivial-tests.md` | `general`, `workflow`, `cleanup`, `testing` |
| `shortcut-review-all-code-specs-docs-convex.md` | `convex`, `workflow` |

#### Agent Setup (`docs/general/agent-setup/`)

| File | Proposed Tags |
|------|---------------|
| `shortcut-setup-beads.md` | `general`, `setup`, `beads` |
| `shortcut-setup-github-cli.md` | `general`, `setup`, `git` |

#### Research (`docs/general/research/current/`)

| File | Proposed Tags |
|------|---------------|
| `research-modern-python-cli-patterns.md` | `python`, `cli`, `research` |
| `research-modern-typescript-cli-patterns.md` | `typescript`, `cli`, `research` |
| `research-modern-typescript-monorepo-patterns.md` | `typescript`, `monorepo`, `research` |
| `research-convex-db-limits-best-practices.md` | `convex`, `research` |
| `research-code-coverage-typescript.md` | `typescript`, `testing`, `research` |
| `research-cli-golden-testing.md` | `cli`, `testing`, `golden-testing`, `research` |

### Tag Taxonomy Summary

| Category | Tags |
|----------|------|
| **Languages** | `python`, `typescript`, `go`, `rust` |
| **Frameworks** | `convex`, `react`, `fastapi`, `django` |
| **Domains** | `testing`, `cli`, `git`, `ci-cd`, `security` |
| **Workflow** | `workflow`, `specs`, `architecture`, `research`, `cleanup` |
| **Testing Types** | `tdd`, `golden-testing`, `di` (dependency injection) |
| **Special** | `general` (language-agnostic), `opinionated`, `beads`, `setup` |

### Implementation Tasks for Metadata

#### Phase 1: Schema & Parsing

- [ ] Create `cli/src/speculate/cli/metadata.py` with:
  - [ ] `DocMetadata` Pydantic model (as defined above)
  - [ ] `Author` Pydantic model
  - [ ] `parse_frontmatter(content: str) -> DocMetadata | None`
  - [ ] `update_frontmatter(content: str, metadata: DocMetadata) -> str`
  - [ ] `validate_frontmatter(path: Path) -> list[str]` (returns validation errors)
- [ ] Unit tests for metadata parsing and validation

#### Phase 2: CLI Commands

- [ ] `speculate tags` - list all tags with file counts
- [ ] `speculate validate` - validate frontmatter in all docs
- [ ] `speculate metadata <path>` - show/edit metadata for a file

#### Phase 3: Add Tags to Existing Docs

- [ ] Create script: `scripts/add-tags.py` for batch tagging
- [ ] Add tags to agent-rules (13 files)
- [ ] Add tags to agent-guidelines (4 files)
- [ ] Add tags to agent-shortcuts (27 files)
- [ ] Add tags to agent-setup (2 files)
- [ ] Add tags to research docs (6 files)
- [ ] Add author attribution to all docs (use git history where possible)
- [ ] Run `speculate validate` to confirm all frontmatter is valid

#### Phase 4: Documentation

- [ ] Update docs-overview.md with metadata schema
- [ ] Document tag taxonomy and conventions
- [ ] Add `speculate tags` output to README or CLI help
