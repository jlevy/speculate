# Speculate

The **Speculate project stucture** is a set of **rules, templates, and shortcut
prompts** for agent-based coding using specifications and other agent coding best
practices.

It also includes a **CLI tool** for installing and updating these Markdown docs within
your own repo, in a way that lets you customize things as you wish but still have the
option to update rules that are improved in the future.

I’ve grown to use this process heavily for some recent projects so have pulled this into
an open source repository.

## Installing the CLI

The `speculate` CLI is published on PyPI as
[speculate-cli](https://pypi.org/project/speculate-cli/).

```bash
# Run directly without installing (recommended for one-time use)
uvx speculate-cli --help

# Or install as a tool for repeated use
uv tool install speculate-cli

# Then run as:
speculate --help
```

If you don’t use [uv](https://docs.astral.sh/uv/), you can also install with pip as
`speculate-cli`.

It is more complex with far more rules than some workflows I’ve seen, but over the past
couple months using it, it seems to give very good results consistency and high code
quality when we’ve used it with recent models in Claude Code and VS Code or Cursor.

The goal of this agent structure is to improve speed *and* quality of development for
individuals teams working with LLM agents in Claude Code, Codex, Cursor, Windsurf, etc.
I’ve primarily used this myself or with one other engineer, so only really have
experience with small teams, but have found it extremely helpful.

## Advantages

The advantages of the Speculate project structure are:

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

## Documentation Layout

All project and development documentation is organized in `docs/`, which follow the
Speculate project structure:

### `docs/development.md` — Essential development docs

- `development.md` — Environment setup and basic developer workflows (building,
  formatting, linting, testing, committing, etc.)

Always read `development.md` first!
Other docs give background but it includes essential project developer docs.

### `docs/general/` — Cross-project rules and templates

General rules that apply to all projects:

- @docs/general/agent-rules/ — General rules for development best practices (general,
  pre-commit, TypeScript, Convex)

- @docs/general/agent-shortcuts/ — Reusable task prompts for agents

- @docs/general/agent-guidelines/ — Guidelines and notes on development practices

### `docs/project/` — Project-specific documentation

Project-specific specifications, architecture, and research docs:

- @docs/project/specs/ — Change specifications for features and bugfixes:

  - `active/` — Currently in-progress specifications

  - `done/` — Completed specifications (historic)

  - `future/` — Planned specifications

  - `paused/` — Temporarily paused specifications

- @docs/project/architecture/ — System design references and long-lived architecture
  docs (templates and output go here)

- @docs/project/research/ — Research notes and technical investigations

## Installing Rules

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

### Claude Code and Codex Setup

The root-level `CLAUDE.md` and `AGENTS.md` files point agents to read rules from
@docs/general/agent-rules/. No additional setup needed.

### Automatic Workflow Activation

The @automatic-shortcut-triggers.md file enables automatic shortcut triggering.
When an agent receives a request, it checks the trigger table and uses the appropriate
shortcut from `docs/general/agent-shortcuts/`.

## Agent Task Shortcuts

Shortcuts in `docs/general/agent-shortcuts/` define reusable workflows.
They are triggered automatically via @automatic-shortcut-triggers.md or can be invoked
explicitly.

### Direct Invocation

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

### Automatic Triggering

When you make a request, the agent should follow rules in
@automatic-shortcut-triggers.md for matching triggers.
For example:

- “Create a plan for user profiles” → triggers @shortcut:new-plan-spec.md

- “Commit my changes” → triggers @shortcut:precommit-process.md →
  @shortcut:commit-code.md

## Feedback?

Would like to get feedback on how this works for you and suggestions for improving it!
My info is on [my profile](https://github.com/jlevy).
Posts or DMs on Twitter are easiest.
