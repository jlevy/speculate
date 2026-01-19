---
close_reason: Unit tests provide equivalent coverage
closed_at: 2026-01-19T07:09:30.577Z
created_at: 2026-01-19T06:55:03.980Z
dependencies: []
id: is-01kfagj89dfs6g74nrck62aagn
kind: task
labels: []
parent_id: is-01kfagg3t87mk6657fafnz1q3r
priority: 2
status: closed
title: Add tryscript golden tests for idempotency
type: is
updated_at: 2026-01-19T07:09:30.578Z
version: 2
---
Create cli/tests/claude-hooks.tryscript.md with golden tests for:

1. First Install - Creates Files
   - speculate install creates .claude directory and files
   - .claude/scripts/ensure-gh-cli.sh exists
   - .claude/settings.json has SessionStart hook

2. Idempotency - Second Install
   - Second install produces no errors
   - No duplicate hooks after second install

3. Merging with Existing Settings
   - Preserves existing hooks when adding ours

4. settings.local.json Never Modified
   - settings.local.json is never touched

Reference: Architecture section of plan-2026-01-17-github-cli-setup-hook.md lines 422-527
