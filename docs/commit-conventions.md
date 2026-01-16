# Commit Conventions

We use [Conventional Commits](https://www.conventionalcommits.org/) with extensions for
agentic development.

## Format

```
<type>[optional scope][!]: <description>

[optional body]

[optional footer(s)]
```

- First line short, ideally 72 characters or less
- Use imperative mood ("Add feature" not “Added feature”)
- No scope by default; only use when disambiguation is needed (e.g., `fix(parser):`)
- For breaking changes: add `!` before `:` AND include `BREAKING CHANGE:` in the footer

## Types

- `feat`: New feature (improved software functionality)
- `fix`: Bug fix (corrected software functionality)
- `docs`: Software documentation (README, API docs, guides)
- `style`: Code formatting (no logic change)
- `refactor`: Code restructuring (no behavior change)
- `test`: Adding or updating tests
- `chore`: Maintenance (deps, config, build, upgrades)
- `plan`: Design documents, architecture plans, requirements, research
- `ops`: Operational tasks (issue tracking, syncing, publishing, maintenance)
- `process`: Changes to development methodology, conventions, policies

Commit types can drive automated versioning and changelogs.
See your project’s release process for specific rules.

The type indicates the *category of artifact* being changed.
Corrections within a category use that category’s type (e.g., fixing a typo in docs is
`docs:`, not `fix:`).

Note: `plan`, `ops`, and `process` are extensions for agentic development, not part of
the standard Conventional Commits spec.
The distinction: `docs` is for users, `plan` is what we intend to build, `ops` is
running the work, and `process` is how we work.

## Examples

```
feat: Add support for custom labels
feat(parser): Add YAML front matter support
fix: Handle empty issue list gracefully
fix(api): Return 404 for missing resources
docs: Update CLI usage examples
docs: Fix typo in API reference
style: Format with prettier
refactor: Extract validation logic to separate module
test: Add golden tests for sync command
chore: Update dependencies
plan: Add design document for dependency resolution
ops: Update issue status for auth feature
ops: Sync beads with remote
process: Add TDD guidelines for agent workflows
```
