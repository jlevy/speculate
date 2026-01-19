---
close_reason: Script created with all required functionality
closed_at: 2026-01-19T06:59:47.370Z
created_at: 2026-01-19T06:54:05.046Z
dependencies:
  - target: is-01kfagh5esb6y4pt032efj76ag
    type: blocks
id: is-01kfaggeqqchn6th836b04yxar
kind: task
labels: []
parent_id: is-01kfagg3t87mk6657fafnz1q3r
priority: 2
status: closed
title: Create ensure-gh-cli.sh script
type: is
updated_at: 2026-01-19T06:59:47.387Z
version: 3
---
Create `.claude/scripts/ensure-gh-cli.sh` in the root docs directory (part of copier template).

The script should:
- Add common binary locations to PATH (~/.local/bin, ~/bin, /usr/local/bin)
- Check if gh is already installed, skip if present
- Detect platform (darwin/linux) and architecture (amd64/arm64)
- Download and install gh to ~/.local/bin
- Use fallback version (2.83.1) if GitHub API is rate-limited
- Verify gh is in PATH after installation
- Check GH_TOKEN authentication, warn but don't fail if missing/invalid
- Always exit 0 (warnings don't block session start

Reference: Architecture section of plan-2026-01-17-github-cli-setup-hook.md lines 167-247
EOF
)
