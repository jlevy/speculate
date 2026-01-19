---
close_reason: "All implementation tasks complete: hook script, settings.json, CLI integration, tests"
closed_at: 2026-01-19T07:09:45.872Z
created_at: 2026-01-19T06:53:53.856Z
dependencies: []
id: is-01kfagg3t87mk6657fafnz1q3r
kind: epic
labels: []
priority: 2
status: closed
title: GitHub CLI Setup Hook Implementation
type: is
updated_at: 2026-01-19T07:09:45.872Z
version: 2
---
Implement automated GitHub CLI setup hook for Speculate that ensures every initialized repository has `gh` CLI available and authenticated for agent sessions.

**Spec:** cli/docs/project/specs/active/plan-2026-01-17-github-cli-setup-hook.md

**Core deliverables:**
1. Shell script (`ensure-gh-cli.sh`) that installs and configures gh CLI
2. Claude Code hook configuration (`.claude/settings.json`)
3. Integration with `speculate install` command
4. Copier template updates
5. Documentation updates (naming consistency)
6. Tests for idempotency and merging behavior
