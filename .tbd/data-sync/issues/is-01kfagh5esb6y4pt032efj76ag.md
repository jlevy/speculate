---
close_reason: Added _setup_claude_hooks() function with script and settings handling
closed_at: 2026-01-19T07:01:34.730Z
created_at: 2026-01-19T06:54:28.312Z
dependencies:
  - target: is-01kfaghb9xt5qgtr86dnfswbh2
    type: blocks
  - target: is-01kfagj0e658am7bmwkwd5kh41
    type: blocks
id: is-01kfagh5esb6y4pt032efj76ag
kind: task
labels: []
parent_id: is-01kfagg3t87mk6657fafnz1q3r
priority: 2
status: closed
title: Add _setup_claude_hooks() to cli_commands.py
type: is
updated_at: 2026-01-19T07:01:34.731Z
version: 4
---
Add new function to cli/src/speculate/cli/cli_commands.py that sets up the .claude/ directory.

Function responsibilities:
- Create .claude/scripts/ directory structure
- Copy or create ensure-gh-cli.sh script
- Create or merge .claude/settings.json (handle existing settings gracefully)
- Never touch .claude/settings.local.json (user local overrides)

Idempotency requirements:
- No .claude/ directory -> create everything
- .claude/ exists, no settings.json -> create settings.json
- settings.json exists, no SessionStart hooks -> add SessionStart array
- settings.json has SessionStart hooks, not ours -> append our hook
- Our hook already present -> skip (no duplicate)
- Script exists and matches -> skip
- Script exists but modified -> skip with warning (preserve user customizations)
- --force flag -> overwrite even if modified

Detection: Identify our hook by checking if command contains ensure-gh-cli.sh

Reference: Architecture section of plan-2026-01-17-github-cli-setup-hook.md lines 272-291
