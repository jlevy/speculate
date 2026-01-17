# Shortcut: New CLI Release

Create and publish a new release of the speculate-cli package to PyPI.

## Prerequisites

1. Read @docs/general/agent-setup/github-cli-setup.md and verify `gh` is working
2. Read @cli/publishing.md for an overview of the release process
3. Read @docs/general/agent-guidelines/release-notes-guidelines.md for release notes
   format

## Instructions

Create a to-do list with the following items then perform all of them:

### 1. Verify Prerequisites

```bash
cd cli
gh auth status  # Confirm gh is authenticated
make lint && make test  # Ensure tests pass
git status  # Must be clean
git push  # Push any pending commits
gh run list -R jlevy/speculate --limit 1  # Verify CI passed
```

### 2. Determine Next Version

```bash
# Check current releases
gh release list -R jlevy/speculate --limit 5

# Review changes since last release
git log $(git describe --tags --abbrev=0 --match "cli-v*" 2>/dev/null || echo "HEAD~20")..HEAD --oneline
```

Choose version bump based on changes:

- `patch`: Bug fixes, docs, internal changes
- `minor`: New features, non-breaking changes
- `major`: Breaking changes

### 3. Write Release Notes

Follow @docs/general/agent-guidelines/release-notes-guidelines.md format:

```markdown
## What's Changed

### Features

- **Feature name**: Brief description

### Fixes

- Fixed specific issue

**Full commit history**: https://github.com/jlevy/speculate/compare/cli-vX.X.X...cli-vY.Y.Y
```

Save to `release-notes.md` or prepare for inline use.

### 4. Create the Release

```bash
# Replace X.X.X with the new version number
gh release create cli-vX.X.X -R jlevy/speculate \
  --title "CLI vX.X.X" \
  --notes-file release-notes.md
```

Or with inline notes:

```bash
gh release create cli-vX.X.X -R jlevy/speculate \
  --title "CLI vX.X.X" \
  --notes "$(cat <<'EOF'
## What's Changed

### Features

- **Feature name**: Description

**Full commit history**: https://github.com/jlevy/speculate/compare/cli-v0.0.8...cli-vX.X.X
EOF
)"
```

### 5. Monitor and Verify

```bash
# Watch the publish workflow
gh run list -R jlevy/speculate --limit 1
gh run watch <run-id> --exit-status

# Verify on PyPI
curl -s https://pypi.org/pypi/speculate-cli/json | python3 -c \
  "import sys,json; print('Published:', json.load(sys.stdin)['info']['version'])"

# Test installation
uv tool install --force speculate-cli
speculate --version
```

### 6. Clean Up

```bash
rm -f release-notes.md  # If created locally
```

## Troubleshooting

- **Workflow not triggered**: Ensure tag is `cli-v*` format
- **PyPI 403 error**: Check trusted publishing at
  https://pypi.org/manage/project/speculate-cli/settings/publishing/
- **Version mismatch**: Tags must follow `cli-v0.0.0` format exactly
