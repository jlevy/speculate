# Publishing (speculate-cli)

This document covers publishing the `speculate-cli` Python package to
[PyPI](https://pypi.org/project/speculate-cli/).

For release notes format, see @docs/general/agent-guidelines/release-notes-guidelines.md.

## Overview

- **Package name**: `speculate-cli` (install with `pip install speculate-cli` or
  `uv add speculate-cli`)
- **Executable**: `speculate`
- **Tag format**: `cli-v0.1.0` (uses `cli-v` prefix since this is a monorepo)
- **Versioning**: Automatic via
  [uv-dynamic-versioning](https://github.com/ninoseki/uv-dynamic-versioning/)

The release workflow uses PyPI trusted publishing (OIDC) - no tokens required.

## One-Time Setup

Before the first release, configure PyPI trusted publishing:

1. **Get a PyPI account** at [pypi.org](https://pypi.org/) and sign in

2. **Configure trusted publishing**:
   - Go to [PyPI publishing settings](https://pypi.org/manage/account/publishing/)
   - Under "Trusted Publisher Management", add a new pending publisher:
     - **Project name**: `speculate-cli`
     - **Owner**: `jlevy`
     - **Repository**: `speculate`
     - **Workflow**: `publish.yml`
     - **Environment**: Leave blank

3. **Verify the workflow exists** at `.github/workflows/publish.yml`

## Release Workflow

See [cli/docs/development.md](docs/development.md#releasing-to-pypi) for the full
release process.

### Quick Reference

```bash
# 1. Ensure tests pass
cd cli
make lint && make test
git push
gh run list --limit 1  # Verify CI passed

# 2. Check current version
gh release list -R jlevy/speculate --limit 3

# 3. Prepare release notes (see release-notes-guidelines.md)
git log $(git describe --tags --abbrev=0 --match "cli-v*" 2>/dev/null || echo "HEAD~20")..HEAD --oneline

# 4. Create release (triggers publish workflow)
gh release create cli-v0.0.9 --title "CLI v0.0.9" --notes-file release-notes.md
# Or with inline notes:
gh release create cli-v0.0.9 --title "CLI v0.0.9" --notes "Brief description"

# 5. Monitor and verify
gh run list --limit 1
gh run watch <run-id> --exit-status

# 6. Confirm on PyPI
curl -s https://pypi.org/pypi/speculate-cli/json | python3 -c \
  "import sys,json; print(json.load(sys.stdin)['info']['version'])"
```

## Version Format

- **Tagged releases**: `cli-v0.1.0` tag produces version `0.1.0` on PyPI
- **Development versions** (between tags): `0.1.1.dev3+g1234567`

## Troubleshooting

**Publish workflow not running?**

- Ensure tag format is `cli-v*` (e.g., `cli-v0.0.9`)
- Check tag was pushed: `git ls-remote --tags origin | grep cli-v`

**PyPI publish failing with 403?**

- Verify trusted publishing is configured at
  https://pypi.org/manage/project/speculate-cli/settings/publishing/
- Ensure the repository and workflow match exactly

**Version not updating?**

- The version is derived from git tags via uv-dynamic-versioning
- Ensure the tag follows the `cli-v0.0.0` format
