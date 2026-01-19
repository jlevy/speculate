---
close_reason: Added SessionStart hook to existing settings.json
closed_at: 2026-01-19T07:00:16.698Z
created_at: 2026-01-19T06:54:11.570Z
dependencies:
  - target: is-01kfagh5esb6y4pt032efj76ag
    type: blocks
id: is-01kfaggn3kqzm80vghmxx21r2a
kind: task
labels: []
parent_id: is-01kfagg3t87mk6657fafnz1q3r
priority: 2
status: closed
title: Create .claude/settings.json template
type: is
updated_at: 2026-01-19T07:00:16.699Z
version: 3
---
Create `.claude/settings.json` in the root docs directory (part of copier template).

Structure:
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

Reference: Architecture section of plan-2026-01-17-github-cli-setup-hook.md lines 249-268
