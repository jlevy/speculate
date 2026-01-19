---
close_reason: Added .claude/ directory to copier whitelist
closed_at: 2026-01-19T07:00:34.339Z
created_at: 2026-01-19T06:54:40.315Z
dependencies: []
id: is-01kfaghh5x0qfj89cfwba8qfjb
kind: task
labels: []
parent_id: is-01kfagg3t87mk6657fafnz1q3r
priority: 2
status: closed
title: Update copier.yml to include .claude/ directory
type: is
updated_at: 2026-01-19T07:00:34.340Z
version: 2
---
Modify copier.yml to include the .claude/ directory in the template.

Current exclude patterns only whitelist docs/ and .speculate/. Need to add:
  - !/.claude
  - !/.claude/**

Reference: copier.yml lines 5-14
