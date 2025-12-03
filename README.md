# Speculate

**Speculate** is a **project structure for spec-driven agent coding**.

It includes **common rules, templates, and shortcut prompts** that help an agent plan
better and write better code and a **CLI tool** that copies and updates these Markdown
docs within your own repo.

The goal of this agent structure is to improve speed *and* quality of development for
individuals teams working with LLM agents in Claude Code, Codex, Cursor, Windsurf, etc.
I’ve primarily used this myself and one other engineer, so we only really have
experience with small teams, but we have found this agent coding structure extremely
helpful.

It is fairly complex, with many rules and checks, but it’s exactly these rules that give
significant improvents in both speed and code quality.
In paricular, at least for our full-stack development work, the workflows here in Claude
Code and Cursor make it possible to ship significant features where almost all the code
is agent written—yet it is not slop code.
You can still read it as well as code by human engineers and if done well, decisions and
architecture is documented much better than when it’s done by most human engineers.

I’ve grown to use these rules and processes heavily and wanted to share rules across
repositories, so have pulled all the reusable rules into this repo as open source.

## Motivation

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

## Notes and Caveats

After using this structure heavily for the past 2-3 months as well as using coding tools
in other ways for the past 2 years, we do have some take-aways:

- Agent coding is changing ridiculously quickly and it has improved a lot just since
  mid-2025. But none of this is foolproof.
  Even the best agents like Claude Sonnet 4.5 and GPT-5 Codex High make really stupid
  errors sometimes.

- Spec-driven development like this is most effective if you’re a fairly senior engineer
  already and can agressively correct the agent during spec writing and when reviewing
  code.

- It is also most effective for full-stack or product engineering, where the main
  challenge is implementing everything in a flexible way.
  Visually intensive frontend engineering and “harder” algorithmic, infrastructure, or
  machine learning engineering still seem better suited to iteratively writing code by
  hand.

- Even if you are writing code by hand, the processes for writing research briefs and
  architecture docs is still useful.
  Agents are great at maintaining docs!

- For product engineering, you can often get away with writing very little code manually
  if the spec docs are reviewed.
  With good templates and examples, you can chat with the agent to write the specs as
  well. But you do have to actually read the spec docs and review the code!

- But with some discipline this appraoch is really powerful.
  Contrary to what some say, we have found it doesn’t lead to buggy, dangerous, and
  unmaintainable code the way blindly vibe coding does.
  And it is much faster than writing the same code fully by hand.

- Avoid testing cycles that are manual!
  It’s best to combine this approach with an architecture that makes testing really
  easy. If at all possible, insist on architectures where all tasks are easy to run from
  the command line. Insist on mockable APIs and databases, so even integration testing is
  easy from the command line.

## Organization and Principles

This repo is largely just a bunch of Markdown docs in a clean organized structure.
We try to keep all docs small to medium sized, for better context management.
If you like, just go read the [docs/](docs/) files and you’ll see how it works.

Shortcut docs reference other docs like templates and rule file docs.
Spec docs like planning specs can reference other docs like architecture docs for
background, without loading a full architecture doc into context unless necessary.

The key insights for this approach are:

- Check in specs and all other process docs as Markdown into your main repository
  alongside the code. A well-organized repository can easily be 30-50% Markdown docs.
  This is fine! You can always archive obsolete docs later but having these helps with
  context management.

- Distinguish between *general* docs and *project-specific* docs, so that you can reuse
  docs across repositories and projects

- Also organize docs into types *by lifecycle*: Most specs are short-lived only during
  implementation, but they reference longer-lived research or architecture docs

- Breakdown specs for planning features, fixes, tasks, or refactors into subtypes: *plan
  specs*, *implementation specs*, *validation specs*, and *bugfix specs*. Typically do
  the planning first, then implementation, which includes the architecture.

- Do heavy amounts of testing during implementation.
  This avoids issues as it progresses.
  Once testing is done, write validation specs that highlight what was covered by unit
  or integration tests and what needs to be tested manually.

- Keep docs *small to moderate size* with plenty of *cross-references* so that it’s easy
  to reference one to three docs as well as certain code files in a single prompt and
  have plenty of context to spare.
  The agent can also read additional docs as needed.

- Orchestrate routine or complex tasks simply as *shortcut doc*, which is just a list of
  3 to 10 sub-tasks, each of which might reference other docs.
  Agents are great at following short to-do lists so all shortcut docs are just ways to
  use these to-do lists with less typing.

## Types of Docs

Speculate maintains docs of several kinds in your repo.

The main types are:

- General **agent rules** for best practices, test-driven development, and rules for
  Python and TypeScript

- **Spec docs** for *planning, implementation, and validation spec.

There are two categories of docs:

- **general docs** that are shared across repos and you typically don’t need to modify

- **project-specific docs** that are only used by the current repo and that you will add
  to routinely

If you have a new doc, you usually add it to project-specific docs initially, then
consider if it goes into the general docs upstream, so you can install it in other
repos.

## CLI Workflows

The CLI workflow is really just a convenience to copy and update docs.
It is helpful in three use cases currently:

- **Initialization:** The first task is to set up initial docs into your repo.
  The `speculate init` command copies of all general docs as Markdown docs into a
  `docs/general` directory in your repo.
  It also sets up a `docs/project` skeleton directory where you can place the
  project-specific docs.

- **Updates:** Another task is to update general docs when they are updated upstream in
  this `jlevy/speculate` repository.
  This is done by copying down files using [copier](https://copier.readthedocs.io/).
  This supports usual git merges, in case docs like rules or templates have been merged
  in your local repo and upstream.

- **Installation:** Agent rules are installed as references in `CLAUDE.md`, `AGENTS.md`,
  and `.cursor/rules`. This is done automatically at both initialization and update time
  and is idempotent.

Most of the time you don’t need to run the CLI at all, and you just reference the docs
inside your agent.

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

## How it Works: A Detailed Example

With just these templates and shortcut docs and disciplined workflows, you can do quite
a few things. Here is an example that shows the main shortcuts and doc types:

- You install the CLI and run `speculate init` from within your repo.
  This copies a bunch of docs into a `docs/` folder.
  (You only do this once but you can also run `speculate update` in the future if you
  want to update docs after the Speculate repo changes.)

- You want to add a new feature or perform a task like a refactor.
  The first step is to plan it.
  Reference
  [shortcut:new-plan-spec.md](docs/general/agent-shortcuts/shortcut:new-plan-spec.md)
  (just hit `@` and type `new-plan` and it’s generally sufficient) and give your agent
  of choice (Claude Code, Codex, or Cursor) an initial description of what you want.
  The agent will read this shortcut doc, follow the listed steps to find the plan spec
  template doc, and fill it in a plan using the information you’ve given.
  You can review and iterate on the spec.
  Because of the shortcut instructions it will be placed at
  `docs/project/specs/active/plan-YYYY-MM-DD-some-feature.md`. Keep chatting and
  reviewing the plan until the it looks like it is a reasonable background, motivation,
  and general architecture changes.

- Typically you’d then do a more detailed implementation plan that pulls in more code
  for context and maps out what parts of the codebase need to change.
  Reference
  [shortcut:new-implementation-spec.md](docs/general/agent-shortcuts/shortcut:new-implementation-spec.md)
  and the agent then copies the implementation spec template and fills that in based on
  what’s been done in the planning spec.

- Once the plan and implementation specs are ready.
  Reference
  [shortcut:implement-spec.md](docs/general/agent-shortcuts/shortcut:implement-spec.md)
  with the spec in context, and it will then begin implementation.

- Say during this process you notice you’ve made some poor architecture choices because
  you didn’t research available libraries or fully reference the right parts of the
  codebase well enough in the implementation plan.
  It’s time to do more research and analysis.
  You reference
  [shortcut:new-research-brief.md](docs/general/agent-shortcuts/shortcut:new-research-brief.md)
  and tell it to research all available alternative libraries and save the research
  brief. Iterate on this doc until satisfied.
  Make sure it has good links and background.

- Now you have an idea of what library to use but are not sure of how many places in the
  codebase need to change.
  Your codebase has gotten quite large and it’s getting confusing, so you tell the agent
  to write a full architecture summary by referencing
  [shortcut:new-architecture-doc.md](docs/general/agent-shortcuts/shortcut:new-architecture-doc.md).
  The agent looks through the codebase and you iterate to improve the architecture doc.

- Now return to your plan spec, reference them, and tell the agent to reference both the
  research brief and the architecture doc, and revise the plan spec, including the
  architecture doc as background.
  Reference
  [shortcut:implement-spec.md](docs/general/agent-shortcuts/shortcut:implement-spec.md).

- Repeat with the implementation plan spec.
  Now we are ready to try implementing again.

- As you go, you want the agent to do more testing.
  Reference rules docs like
  [general-tdd-guidelines.md](docs/general/agent-guidelines/general-tdd-guidelines.md)
  and tell it to be stricter about test-driven development.

- Finally you’re at an initial stopping point and tests are passing.
  Reference
  [shortcut:commit-code.md](docs/general/agent-shortcuts/shortcut:commit-code.md) to
  commit. These instructions tell the agent to

  1. Run all linting and tests and fix everything

  2. Review code and make sure it complies with relevant coding rules

  3. Run all tests again after review edits

  4. Backfill the specs so we know they are in sync with the code that is committed

  5. Commit the code (fixing any commit hooks if something slipped through)

- Repeat the processes above until the feature is getting complete.
  Reference
  [shortcut:new-validation-spec.md](docs/general/agent-shortcuts/shortcut:new-validation-spec.md)
  to have it write a spec of what automated testing has been done and what needs to be
  manually validated by you.

- Reference [shortcut:create-pr.md](docs/general/agent-shortcuts/shortcut:create-pr.md)
  to request the agent do a final review of all code on your branch and use `gh` to file
  a PR that references the relevant parts of the validation spec.
  You can now review the PR again, do manual testing, repeat the above steps as desired.

- During this whole process, you can add more agent rules, research docs, template
  improvements, etc. Agent coding is best when you iteratively improve processes all the
  time!

- Finally, you can run `speculate update` to get updates to the shared general structure
  in this repo. Conflicts are detected and you can deal with merges.

That’s a bit complex.
But it is also quite powerful.
By now I hope you see how all these docs work together in a structure to make agent
coding quite fast *and* the quality of code higher.

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

## Installing to Claude Code, Codex, and Cursor

The source of truth for all rules is `docs/general/agent-rules/`. These rules are
consumed by different tools via their native configuration formats:

| Tool | Configuration File | How Rules Are Loaded |
| --- | --- | --- |
| **Cursor** | `.cursor/rules/*.md` | Symlink or copy from `docs/` |
| **Claude Code** | `CLAUDE.md` | Points to `docs/` directory |
| **Codex** | `AGENTS.md` | Points to `docs/` directory |

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
