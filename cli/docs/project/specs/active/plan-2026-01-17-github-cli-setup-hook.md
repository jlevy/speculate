# Plan Spec: GitHub CLI Setup Hook for Speculate

## Purpose

This is a technical design doc for adding an automated GitHub CLI setup hook to
Speculate that ensures every initialized repository has `gh` CLI available and
authenticated for agent sessions.

## Background

The GitHub CLI (`gh`) is essential for agent-based development workflows.
Without it, agents cannot:
- Create pull requests (`gh pr create`)
- View and comment on issues (`gh issue`)
- Interact with GitHub’s API for code review workflows
- Use GitHub Actions and other CI/CD integrations

Currently, there’s no standard way in Speculate to ensure `gh` is available.
This creates friction when starting new repositories or onboarding new environments.

### Reference Implementation

The script at `ai-trade-arena/.claude/scripts/ensure-gh-cli.sh` provides a working
reference that:
- Adds common binary locations to PATH
- Detects if `gh` is installed, installing it if needed (cross-platform)
- Verifies authentication status via `GH_TOKEN`

### Environment Variables Required

Based on research into GitHub CLI authentication:

| Variable | Purpose | Required? |
| --- | --- | --- |
| `GH_TOKEN` | Personal access token for authentication | Yes |
| `GH_PROMPT_DISABLED=1` | Prevents interactive prompts in automated contexts | Yes |

### Personal Access Token Research

**GitHub recommends fine-grained tokens over classic tokens** for better security:

**Fine-Grained Token Advantages:**
- Scoped to specific repositories or organizations
- Granular permission control
- Required expiration dates
- Better audit trail

**Fine-Grained Token Limitations:**
- Does not support GraphQL API (critical for some `gh` operations)
- Cannot access repositories where user is only an outside collaborator
- Cannot access multiple organizations at once

**Recommendation for Speculate users:**
- For most use cases, **fine-grained tokens** should work
- Minimum permissions needed: `repo` access to target repositories
- If users need GraphQL operations or cross-org access, they’ll need **classic tokens**
  with scopes: `repo`, `read:org`, `gist`

Sources:
- [GitHub Docs: Managing Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [GitHub Blog: Introducing Fine-Grained PATs](https://github.blog/security/application-security/introducing-fine-grained-personal-access-tokens-for-github/)
- [GitHub CLI Auth Documentation](https://cli.github.com/manual/gh_auth_login)

## Summary of Task

Add a GitHub CLI setup hook to Speculate that:

1. **Is included in every initialized repo** via `speculate init`
2. **Is safe and idempotent** - can run multiple times without side effects
3. **Works in any environment** - macOS, Linux, cloud environments
4. **Documents required environment variables** clearly
5. **Integrates with Claude Code hooks** via `.claude/settings.json`

## Backward Compatibility

### User-Facing Changes

| Area | Before | After | Migration |
| --- | --- | --- | --- |
| `speculate init` | No gh setup | Installs hook and docs | None required |
| Existing repos | No hook | Must run `speculate install` or manually add | Manual step |

### Breaking Changes

None. This is a new feature.

## Stage 1: Planning Stage

### Design Decisions

Based on user clarification:

1. **Hook Trigger**: `SessionStart` only - runs once when Claude Code session begins
2. **Installation Behavior**: Auto-install silently to `~/.local/bin` without prompting
3. **Token Documentation**: Both - detailed
   `docs/general/agent-setup/github-cli-setup.md` AND inline script comments
4. **Env Setup**: Documentation only (no `.env.example`) - explain where to set
   environment variables in different contexts (Claude Code Cloud settings, shell
   profile, etc.)

### Requirements

**Must Have:**
- [ ] Shell script that ensures `gh` is installed and in PATH
- [ ] Cross-platform support (macOS, Linux x86_64, Linux arm64)
- [ ] Idempotent execution (safe to run multiple times)
- [ ] Clear error messages when GH_TOKEN is missing
- [ ] Integration with `speculate init` to install hook automatically
- [ ] Documentation of required environment variables

**Should Have:**
- [ ] Integration with `speculate install` for existing repos
- [ ] Warning output when authentication fails
- [ ] Fallback version number if GitHub API rate-limited

**Not In Scope:**
- Windows support (can add later)
- Interactive token generation wizard
- OAuth browser-based authentication flow
- Support for GitHub Enterprise (different API endpoints)

### Acceptance Criteria

1. Running `speculate init` on a new project includes the gh setup hook
2. Opening a Claude Code session with the hook runs gh verification
3. If `gh` is missing, it gets installed to `~/.local/bin`
4. If `GH_TOKEN` is missing, user sees clear message with setup instructions
5. Running the hook twice produces no errors and no duplicate installations
6. Documentation clearly explains how to get and set GH_TOKEN

## Stage 2: Architecture Stage

### Current State Analysis

**Existing GitHub CLI documentation:**
- `docs/general/agent-setup/github-cli-setup.md` - Manual setup instructions
- This will be enhanced, not replaced

**Existing Claude Code hook pattern** (from `attic/markform/`):
- `.claude/settings.json` defines hooks
- `.claude/scripts/` contains shell scripts
- `.claude/hooks/` for session-specific hooks
- Scripts use `$CLAUDE_PROJECT_DIR` and `$CLAUDE_ENV_FILE` environment variables

**Speculate CLI commands:**
- `init()` in `cli_commands.py:52` - Creates new project, calls `install()`
- `install()` in `cli_commands.py:185` - Sets up tool configs (CLAUDE.md, .cursor/rules,
  etc.)

### Proposed Architecture

#### Files to Create

**Source files** (in CLI package resources):

| File | Purpose |
| --- | --- |
| `cli/src/speculate/cli/resources/claude-hooks/scripts/ensure-gh-cli.sh` | Hook script template |
| `cli/src/speculate/cli/resources/claude-hooks/hooks.json` | Hook definitions to merge into settings.json |

**Output files** (created by `speculate install`):

| File | Purpose |
| --- | --- |
| `.claude/scripts/ensure-gh-cli.sh` | Hook script that ensures gh is installed and authenticated |
| `.claude/settings.json` | Claude Code hook configuration (merged, not replaced) |

#### Files to Modify

| File | Changes |
| --- | --- |
| `docs/general/agent-setup/github-cli-setup.md` | Rename from `github-cli-setup.md`, restructure for human setup guide |
| `cli/src/speculate/cli/cli_commands.py` | Add `.claude/` setup to `install()` |

**Important**: `copier.yml` should **NOT** include `.claude/` in its whitelist. The `.claude/`
directory is set up programmatically by `_setup_claude_hooks()` which properly merges settings
instead of overwriting. This ensures:
- User customizations in `.claude/settings.json` are preserved
- `.claude/settings.local.json` is never touched
- Project-specific hooks (like speculate's own `tbd-closing-reminder.sh`) don't get copied to new projects

### Hook Script Design (`ensure-gh-cli.sh`)

Based on the reference implementation, the script will:

```bash
#!/bin/bash
# GitHub CLI Setup Hook for Claude Code
# Runs on SessionStart to ensure gh is available and authenticated
#
# Required environment variables:
#   GH_TOKEN - GitHub personal access token
#   GH_PROMPT_DISABLED=1 - Prevents interactive prompts
#
# See: docs/general/agent-setup/github-cli-setup.md

set -e

# Add common binary locations to PATH
export PATH="$HOME/.local/bin:$HOME/bin:/usr/local/bin:$PATH"

# Check if gh is installed
if command -v gh &> /dev/null; then
    echo "[gh] CLI found at $(which gh)"
else
    echo "[gh] Installing GitHub CLI..."

    # Detect platform
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    [ "$ARCH" = "x86_64" ] && ARCH="amd64"
    [ "$ARCH" = "aarch64" ] && ARCH="arm64"

    # Get latest version (with fallback)
    GH_VERSION=$(curl -fsSL https://api.github.com/repos/cli/cli/releases/latest 2>/dev/null \
        | grep -o '"tag_name": *"v[^"]*"' | head -1 | sed 's/.*"v\([^"]*\)".*/\1/')
    GH_VERSION=${GH_VERSION:-2.83.1}

    # Download based on OS
    if [ "$OS" = "darwin" ]; then
        DOWNLOAD_URL="https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_macOS_${ARCH}.zip"
        curl -fsSL -o /tmp/gh.zip "$DOWNLOAD_URL"
        unzip -q /tmp/gh.zip -d /tmp
        EXTRACT_DIR="/tmp/gh_${GH_VERSION}_macOS_${ARCH}"
    else
        DOWNLOAD_URL="https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_${OS}_${ARCH}.tar.gz"
        curl -fsSL -o /tmp/gh.tar.gz "$DOWNLOAD_URL"
        tar -xzf /tmp/gh.tar.gz -C /tmp
        EXTRACT_DIR="/tmp/gh_${GH_VERSION}_${OS}_${ARCH}"
    fi

    # Install to ~/.local/bin
    mkdir -p ~/.local/bin
    cp "${EXTRACT_DIR}/bin/gh" ~/.local/bin/gh
    chmod +x ~/.local/bin/gh
    rm -rf "${EXTRACT_DIR}" /tmp/gh.zip /tmp/gh.tar.gz 2>/dev/null || true

    echo "[gh] Installed to ~/.local/bin/gh"
fi

# Verify gh is in PATH
if ! command -v gh &> /dev/null; then
    echo "[gh] ERROR: gh not found in PATH after installation"
    echo "[gh] Add ~/.local/bin to your PATH"
    exit 1
fi

# Check authentication
if [ -n "$GH_TOKEN" ]; then
    if gh auth status &> /dev/null; then
        echo "[gh] Authenticated successfully"
    else
        echo "[gh] WARNING: GH_TOKEN set but authentication failed"
        echo "[gh] Token may be invalid or expired"
    fi
else
    echo "[gh] WARNING: GH_TOKEN not set"
    echo "[gh] See: docs/general/agent-setup/github-cli-setup.md"
fi

exit 0
```

### Settings.json Structure

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/scripts/ensure-gh-cli.sh",
            "timeout": 120
          }
        ]
      }
    ]
  }
}
```

### Integration with `speculate install`

**Already implemented** in `cli_commands.py:620-741`. The function:

1. Loads hook scripts from `cli/src/speculate/cli/resources/claude-hooks/scripts/`
2. Copies scripts to `.claude/scripts/` (skips if user-modified, unless `--force`)
3. Loads hook definitions from `cli/src/speculate/cli/resources/claude-hooks/hooks.json`
4. Merges hook definitions into `.claude/settings.json` (preserves existing hooks)
5. Never touches `.claude/settings.local.json`

```python
# Key functions (see cli_commands.py for full implementation):
def _setup_claude_hooks(project_root: Path, force: bool = False) -> None:
    """Set up .claude/ directory with hooks from resources."""
    # Copies scripts, merges settings.json

def _copy_script_file(dest_file: Path, content: str, force: bool) -> str | None:
    """Copy script, skip if user-modified (unless force)."""

def _merge_claude_settings(settings_file: Path, hooks_to_add: dict) -> str | None:
    """Merge hook definitions, detect duplicates by command string."""
```

## Stage 3: Refine Architecture

### Reusable Components

1. **Hook script pattern**: The `ensure-gh-cli.sh` script follows the same pattern as
   `attic/markform/.claude/hooks/session-start.sh` - idempotent, platform detection,
   silent installation

2. **Settings.json merging**: Need to handle case where user already has a
   `.claude/settings.json` with custom hooks - should merge, not replace

3. **Environment variable documentation**: The existing
   `docs/general/agent-setup/github-cli-setup.md` already documents GH_TOKEN - we’ll
   enhance rather than duplicate

### Simplifications

1. **Single script**: Keep everything in one `ensure-gh-cli.sh` rather than splitting
   into multiple scripts

2. **No version pinning**: Use latest gh version by default (with fallback) rather than
   requiring updates

3. **No remote-only mode**: Unlike the Node.js example, gh CLI is useful in both local
   and remote environments, so don’t gate on `CLAUDE_CODE_REMOTE`

### Idempotency and Safety Guarantees

The implementation must be safe to run multiple times and in any Claude Code
environment.

#### Hook Script (`ensure-gh-cli.sh`)

| Scenario | Behavior |
| --- | --- |
| `gh` already installed (system or ~/.local/bin) | Skip installation, print location |
| `gh` missing | Install to ~/.local/bin |
| `GH_TOKEN` set and valid | Print success |
| `GH_TOKEN` set but invalid | Print warning, continue (don't fail) |
| `GH_TOKEN` not set | Print warning with doc link, continue (don't fail) |
| No network access | Fail gracefully with clear error |
| GitHub API rate-limited | Use fallback version (2.83.1) |

**Key**: Script always exits 0 unless `gh` install fails - warnings don’t block session
start.

#### Settings.json Merging (`speculate install`)

| Scenario | Behavior |
| --- | --- |
| No `.claude/` directory | Create directory and settings.json |
| `.claude/` exists, no settings.json | Create settings.json |
| settings.json exists, no SessionStart hooks | Add SessionStart array with our hook |
| settings.json has SessionStart hooks, not ours | Append our hook to existing array |
| settings.json already has our hook | Skip (no duplicate) |
| `.claude/settings.local.json` exists | Never touch - user's local overrides |

**Detection**: Identify “our hook” by checking if command contains `ensure-gh-cli.sh`.

#### Script File Management

| Scenario | Behavior |
| --- | --- |
| Script doesn't exist | Create it |
| Script exists, matches template | Skip (already up to date) |
| Script exists, user modified | **Skip** with warning (preserve customizations) |
| `--force` flag passed | Overwrite even if modified |

**Detection**: Compare script content hash or check for a version marker comment.

### Edge Cases

1. **gh already in system PATH**: Skip installation silently (idempotent)

2. **Rate-limited GitHub API**: Fallback version number ensures script doesn’t fail

3. **No network access**: Script should fail gracefully with clear error message

4. **Concurrent runs**: File operations should be atomic where possible

5. **Partial installation**: If script exists but settings.json doesn’t reference it,
   add the reference

## Stage 4: Implementation

**Status**: Phases 1-2 are complete. The core hook, script, and CLI integration are
implemented. Remaining work is documentation updates and testing.

### Phase 1: Core Hook and Script

**Tasks:**
- [x] Create `cli/src/speculate/cli/resources/claude-hooks/scripts/ensure-gh-cli.sh`
- [x] Create `cli/src/speculate/cli/resources/claude-hooks/hooks.json` (hook definitions)
- [ ] Test hook works on macOS (darwin/amd64, darwin/arm64)
- [ ] Test hook works on Linux (linux/amd64, linux/arm64)

### Phase 2: CLI Integration

**Tasks:**
- [x] Add `_setup_claude_hooks()` function to `cli_commands.py`
- [x] Call from `install()` function
- [x] Handle merging with existing `.claude/settings.json`
- [x] Ensure `copier.yml` does NOT include `.claude/` (handled programmatically)

### Phase 3: Documentation

**Tasks:**
- [ ] Rename `docs/general/agent-setup/shortcut-setup-github-cli.md` to
  `github-cli-setup.md`
- [ ] Restructure documentation:
  - Remove manual installation section (hook handles this automatically)
  - Add note that installation is now automatic via SessionStart hook
  - Add **“Setting Up GH_TOKEN”** section with:
    - Token creation walkthrough (fine-grained vs classic guidance)
    - **Where to set environment variables:**
      - Claude Code Cloud: Environment settings in the web UI
      - Claude Code CLI: Shell profile (`~/.zshrc`, `~/.bashrc`)
      - Other agent environments: Their respective env configuration
  - Keep usage examples (still valuable for agents)
  - Add troubleshooting section
- [ ] Rename `docs/*.sample.md` -> `*.example.md` for naming consistency:
  - `docs/development.npm.sample.md` -> `docs/development.npm.example.md`
  - `docs/publishing.npm.sample.md` -> `docs/publishing.npm.example.md`

### Phase 4: Testing

**Tasks:**
- [ ] Add unit tests for `_setup_claude_hooks()` in `test_cli_commands.py`
- [ ] Add tryscript golden tests for idempotency (`cli/tests/claude-hooks.tryscript.md`)
- [ ] Manual test: open Claude Code session, verify hook runs

#### Tryscript Test File: `cli/tests/claude-hooks.tryscript.md`

```markdown
---
sandbox: true
env:
  NO_COLOR: "1"
path:
  - $TRYSCRIPT_PROJECT_ROOT/cli/.venv/bin
fixtures:
  - source: $TRYSCRIPT_PROJECT_ROOT/docs
    dest: docs
---

# Claude Hooks Setup Tests

Tests for `speculate install` creating `.claude/` hooks idempotently.

## First Install - Creates Files

# Test: First install creates .claude directory and files

\`\`\`console
$ speculate install
Installing tool configurations...
[..]
? 0
\`\`\`

# Test: .claude/scripts/ensure-gh-cli.sh exists

\`\`\`console
$ test -f .claude/scripts/ensure-gh-cli.sh && echo "exists"
exists
? 0
\`\`\`

# Test: .claude/settings.json has SessionStart hook

\`\`\`console
$ grep -q "ensure-gh-cli.sh" .claude/settings.json && echo "found"
found
? 0
\`\`\`

## Idempotency - Second Install

# Test: Second install produces no errors

\`\`\`console
$ speculate install
Installing tool configurations...
[..]
? 0
\`\`\`

# Test: No duplicate hooks after second install

\`\`\`console
$ grep -c "ensure-gh-cli.sh" .claude/settings.json
1
? 0
\`\`\`

## Merging with Existing Settings

# Test: Preserves existing hooks when adding ours

\`\`\`console
$ cat > .claude/settings.json << 'EOF'
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'user hook'"
          }
        ]
      }
    ]
  }
}
EOF
$ speculate install
[..]
$ grep -c "user hook" .claude/settings.json
1
$ grep -c "ensure-gh-cli.sh" .claude/settings.json
1
? 0
\`\`\`

## settings.local.json Never Modified

# Test: settings.local.json is never touched

\`\`\`console
$ echo '{"user": "config"}' > .claude/settings.local.json
$ speculate install
[..]
$ cat .claude/settings.local.json
{"user": "config"}
? 0
\`\`\`
```

## Stage 5: Validation

**Validation Checklist:**

Hook Script:
- [ ] Hook installs gh if missing on macOS
- [ ] Hook installs gh if missing on Linux
- [ ] Hook detects existing gh and skips installation
- [ ] Hook warns (but doesn’t fail) if GH_TOKEN not set
- [ ] Hook warns (but doesn’t fail) if GH_TOKEN is invalid
- [ ] Hook exits 0 on all warning scenarios (doesn’t block session)
- [ ] Hook handles network failure gracefully

Idempotency - Running `speculate install` multiple times:
- [ ] First run: creates `.claude/scripts/ensure-gh-cli.sh`
- [ ] First run: creates `.claude/settings.json` with SessionStart hook
- [ ] Second run: no changes, no errors, no duplicates
- [ ] Third run: still no changes

Settings.json Merging:
- [ ] Empty `.claude/settings.json` → adds our hook
- [ ] Existing SessionStart hooks → appends ours, preserves others
- [ ] Our hook already present → skips (no duplicate)
- [ ] `.claude/settings.local.json` → never modified

Script File Safety:
- [ ] User-modified script → skip with warning (preserve customizations)
- [ ] `--force` flag → overwrites even if modified
- [ ] Unmodified script → updates if template changed

General:
- [ ] `speculate init` creates all files correctly
- [ ] `speculate install` on existing repo works without breaking config
- [ ] Documentation is clear and complete
- [ ] All existing tests still pass
