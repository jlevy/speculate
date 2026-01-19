---
close_reason: Added call to _setup_claude_hooks from install() and updated docstring
closed_at: 2026-01-19T07:01:56.981Z
created_at: 2026-01-19T06:54:34.300Z
dependencies:
  - target: is-01kfagj89dfs6g74nrck62aagn
    type: blocks
id: is-01kfaghb9xt5qgtr86dnfswbh2
kind: task
labels: []
parent_id: is-01kfagg3t87mk6657fafnz1q3r
priority: 2
status: closed
title: Call _setup_claude_hooks() from install()
type: is
updated_at: 2026-01-19T07:01:56.982Z
version: 3
---
Modify the install() function in cli/src/speculate/cli/cli_commands.py to call _setup_claude_hooks().

Should be called after _setup_cursor_rules() at the end of the install function (around line 250).

Reference: cli_commands.py:185-254
