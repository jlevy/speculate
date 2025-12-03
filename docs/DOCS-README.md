# Human and Agent Development Docs

This folder holds docs and rules for use by humans and LLMs/agents.

## Motivation

The goal of this doc structure is to have development system that can improve speed of
development for one or more developers working with a variety of LLMs/agents such as
Cursor, Windsurf, Claude Code, Codex, etc.

The advantages of the system are:

- **Shared context:** As multiple human developers both work with LLMs, it allows all
  people and tools to have appropriate context

- **Decomposition of tasks:** By decomposing common tasks in to clear, well-organized
  processes, it allows greater flexibility in reusing instructions and rules

- **Reduced context:** Decomposition allows smaller context and this allows more
  reliable adherence to rules and guardrails

This avoids common pitfalls when developing with LLMs:

- Losing track of context on larger features or bugfixes

- Identifying ambiguous features early and clarifying with the user

- Using wrong tools or not following processes appropriate to a given project

- Using wrong or out of date SDKs

- Making poorly thought through architectural choices that lead to needless complication

## Multi-Tool Architecture

The source of truth for all rules is `docs/general/agent-rules/`. These rules are
consumed by different tools via their native configuration formats:

| Tool | Configuration File | How Rules Are Loaded |
| --- | --- | --- |
| **Cursor** | `.cursor/rules/*.md` | Symlink or copy from `docs/` |
| **Claude Code** | `CLAUDE.md` | Points to `docs/` directory |
| **Codex** | `AGENTS.md` | Points to `docs/` directory |
| **Windsurf** | `.windsurfrules` | Copy relevant rules |

### Cursor Setup

For Cursor, create symlinks from `.cursor/rules/` to the docs:

```bash
mkdir -p .cursor/rules
cd .cursor/rules
ln -s ../../docs/general/agent-rules/*.md .
```

### Claude Code / Codex Setup

The root-level `CLAUDE.md` and `AGENTS.md` files point agents to read rules from
@docs/general/agent-rules/. No additional setup needed.

### Automatic Workflow Activation

The @automatic-shortcut-triggers.md file enables automatic shortcut triggering.
When an agent receives a request, it checks the trigger table and uses the appropriate
shortcut from `docs/general/agent-shortcuts/`.

## Documentation Layout

All project and development documentation is organized in `docs/`:

### `docs/general/` — Cross-project rules and templates

General rules that apply to all projects:

- @docs/general/agent-rules/ — General rules for development best practices (general,
  pre-commit, TypeScript, Convex)

- @docs/general/agent-shortcuts/ — Reusable task prompts for agents

- @docs/general/notes/ — Guidelines and notes on development practices

### `docs/project/` — Project-specific documentation

Project-specific rules, workflows, specifications, and architecture:

- `development.md` — Environment setup, maintenance, migrations (copy from
  @docs/project/development.sample.md)

- @docs/project/architecture/ — System design references and long-lived architecture
  docs (templates and output go here)

- @docs/project/specs/ — Change specifications for features and bugfixes:

  - `active/` — Currently in-progress specifications

  - `done/` — Completed specifications (historic)

  - `future/` — Planned specifications

  - `paused/` — Temporarily paused specifications

- @docs/project/research/ — Research notes and technical investigations

## Agent Task Shortcuts

Shortcuts in `docs/general/agent-shortcuts/` define reusable workflows.
They are triggered automatically via @automatic-shortcut-triggers.md or can be invoked
explicitly.

### Automatic Triggering

When you make a request, the agent should follow rules in
@automatic-shortcut-triggers.md for matching triggers.
For example:

- “Create a plan for user profiles” → triggers @shortcut:new-plan-spec.md

- “Commit my changes” → triggers @shortcut:precommit-process.md →
  @shortcut:commit-code.md

### Manual Invocation

You can also invoke shortcuts explicitly:

- @shortcut:new-plan-spec.md — Create a new feature plan

- @shortcut:new-implementation-spec.md — Create an implementation spec

- @shortcut:new-validation-spec.md — Create a validation spec

- @shortcut:new-research-brief.md — Create a new research brief

- @shortcut:new-architecture-doc.md — Create a new architecture document

- @shortcut:revise-architecture-doc.md — Revise an existing architecture document

- @shortcut:implement-spec.md — Implement from an existing spec

- @shortcut:precommit-process.md — Run pre-commit checks

- @shortcut:commit-code.md — Prepare commit message

- @shortcut:create-pr.md — Create a pull request

### Bugfixes

Copy @docs/project/specs/template-bugfix.md to @docs/project/specs/active/ and fill it
in.
