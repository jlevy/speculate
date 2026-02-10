# Speculate

> [!TIP]
>
> Start by reading my (late 2025) post
> **[Lessons from 500K Lines of Spec-Driven Agent Coding](about/lessons_in_spec_coding.md)** 
> for motivation on on why you should write specs.

> [!WARNING]
>
> All this is evolving fast! Most of the rules, docs, and templates are now automatically included in
> my newer tool, [**tbd**](https://github.com/jlevy/tbd). The content here is still good but tbd offers these docs and workflows plus issue tracking (beads) and is now (Feb 2026) how I do all development.

**Speculate** is a **project structure for spec-driven agent coding**.

Speculate give you some **common rules, templates, and shortcut prompts** (in the
[docs/](docs/) folder) that help any coding agent like Claude Code, Codex, or Cursor
plan better using specs, follow more defined processes that result in better code.
You can browse these in the [docs/](docs/) folder.

Speculate also includes a **CLI tool**, `speculate`, that helps copy and update these
Markdown docs within your own repo.

The goal of this structure is to improve development *and* quality of code.

You can use these docs however you like, but I find it is the combination of workflows
that really adds benefit.
It is likely a good fit for individual senior engineers or small teams who want the
velocity of writing lots of code with agents but still need sustainable, good
engineering that won’t fall apart as a codebase grows in complexity.

## Quick Start

1. **Install the CLI**:

   Use [uv](https://docs.astral.sh/uv/):

   ```bash
   uv tool install --upgrade speculate-cli
   ```

2. **Initialize Speculate in your repo:**

   ```bash
   speculate init
   ```

   This copies all general docs (rules, shortcuts, templates) into `docs/general/`,
   creates a `docs/project/` skeleton for your project-specific specs and architecture,
   and configures your agent tools (`CLAUDE.md`, `AGENTS.md`, `.cursor/rules/`
   symlinks). It’s safe to run multiple times (idempotent)—it only adds to existing
   files.

3. **Create your `development.md`:** ← ⚠️ Don’t forget this step!

   Before pointing agents at your repo, make sure **`docs/development.md`** holds your
   key developer workflow docs.
   You may already have this, or see
   **[`docs/development.npm.sample.md`](docs/development.npm.sample.md)** for an
   example. Agents read this file first to understand how to build and test your project.

4. **Start using shortcuts:**

   Reference **`@shortcut-new-plan-spec.md`** to plan a feature,
   **`shortcut-new-implementation-spec.md`** to design the implementation, then
   **`@shortcut-implement-spec.md`** to implement, **`@shortcut-commit-code.md`** to
   commit.

## Agent Docs Layout

Most of this repo is just a “skeleton” structure for docs plus a bunch of suggested
rules and shortcut docs.

### Key Docs

- **[`docs/docs-overview.md`](docs/docs-overview.md)** (**`docs/docs-overview.md`**) is
  a high-level roadmap of every rule, shortcut, and spec.
  The general agent rules should always point to this first.

- **`docs/development.md`** is your concise project-specific setup.
  It should cover your key developer workflows to format, lint, test, and release.
  A sample (**[`docs/development.npm.sample.md`](docs/development.npm.sample.md)**)
  ships in the repo; copy or rewrite it as **`docs/development.md`** and keep it current
  so agents know how to build and validate the project.

### Folder Structure

```
docs/
├── development.md              # Start here! Setup, build, lint, test workflows
├── docs-overview.md            # Summary for agents to read first
│
├── general/                    # Shared across repos (synced via `speculate update`)
│   ├── agent-rules/            # Coding standards and best practices
│   │   ├── general-coding-rules.md
│   │   ├── general-testing-rules.md
│   │   ├── typescript-rules.md
│   │   ├── python-rules.md
│   │   └── ...
│   ├── agent-shortcuts/        # Task prompts (shortcut-*.md)
│   │   ├── shortcut-new-plan-spec.md
│   │   ├── shortcut-implement-spec.md
│   │   ├── shortcut-commit-code.md
│   │   └── ...
│   ├── agent-guidelines/       # Longer guidance docs (TDD, DI, testing)
│   └── agent-setup/            # Tool setup guides for agents
│       ├── github-cli-setup.md
│       ├── beads-setup.md
│       └── ...
│
└── project/                    # Project-specific (you add/edit these)
    ├── specs/                  # Short-lived feature/task specs
    │   ├── active/             # In-progress specs
    │   ├── done/               # Completed (archived)
    │   ├── future/             # Planned
    │   ├── paused/             # On hold
    │   ├── template-plan-spec.md
    │   ├── template-implementation-spec.md
    │   ├── template-validation-spec.md
    │   └── template-bugfix.md
    ├── architecture/           # Long-lived system design docs
    │   ├── current/
    │   ├── archive/
    │   └── template-architecture.md
    └── research/               # Long-lived research and investigations
        ├── current/
        ├── archive/
        └── template-research-brief.md
```

## Types of Docs

The Speculate structure has folders for several kinds in your repo.

All docs fall into two categories:

- **general docs** (`docs/general`) that are shared across repos and you typically don’t
  need to modify

- **project-specific docs** (`docs/project`) that are only used by the current repo and
  that you will add to routinely

If you have a new doc, you usually add it to project-specific docs initially, then
consider if it goes into the general docs upstream, so you can install it in other
repos.

Then there are several kinds of docs:

- **Spec docs** (`docs/project/specs/`) for detailed planning, implementation, and
  validation. Sometimes a single doc is enough but for complex work, each phase should
  probably be a doc of its own, to manage context size.

  - These last only a few days usually, and can be archived by moving them to the
    `docs/project/specs/done/` folder once they are done.

  - In our workflows, we usually have three, each with a prefix and a date
    (**`plan-YYYY-MM-DD-*.md`**, **`impl-YYYY-MM-DD-*.md`**,
    **`valid-YYYY-MM-DD-*.md`**).

  - A good length is 500-800 lines of (linewrapped) Markdown: small enough both you and
    the agent can read fairly quickly.

- **Research briefs** (`docs/project/research/`) to assemble the results of web or other
  research and consolidate it with insights from the codebase or user needs.
  For example, if you are dealing with rate limiting, you should have a research doc on
  all the rate limits of all providers you use as well as the best libraries to use for
  rate limiting.

  - They are long-lived but may not be maintained unless needed.

  - These can be any length but can link heavily.
    They need to be exhaustive at least in terms of links.

- **Architecture docs** to give an overview of all aspects of the system, linking to all
  the relevant parts of the codebase and all relevant libraries that are used.

  - They are long lived and should be regularly maintained.

  - They should not be too long (>2000 lines) so they can be read into context and then
    used for additional planning.

- **Agent rules** (`docs/general/agent-rules/`) for best practices, test-driven
  development, and rules for Python and TypeScript coding.
  For these, the more the better, if they are good rules.
  The only challenge is you need each doc to be manageable size, and bring them into
  context only at the right time to enforce the rules.

  - These are long-lived and should be improved regularly

- **Agent shortcuts** (`docs/general/agent-shortcuts/`) for common processes.
  Thes are simpliy very small Markdown docs with an outline of typically 3–10 steps.
  They can reference other agent rule docs.
  Agents are quite good at using checklists of this length so it is generally sufficient
  just to tag a doc and it will do the right thing.

  - These are long-lived and should be expanded and improved regularly.

- **Agent setup docs** (`docs/general/agent-setup/`) for tool setup and configuration.
  These are step-by-step guides that help agents install and configure tools they need.
  This is especially important for cloud-based environments like Claude Code Cloud that
  don’t have tools like `gh` (GitHub CLI) and `bd` (beads) working initially.

  - These are long-lived and should be updated as tools evolve.

You can reference any of these docs as needed in chat.
The most common pattern is simply to mention the shortcut docs.
For example, the key ones are:

- **@shortcut-new-plan-spec.md** — Create a new feature plan

- **@shortcut-new-implementation-spec.md** — Create an implementation spec

- **@shortcut-new-validation-spec.md** — Create a validation spec

- **@shortcut-new-research-brief.md** — Create a new research brief

- **@shortcut-new-architecture-doc.md** — Create a new architecture document

- **@shortcut-revise-architecture-doc.md** — Revise an existing architecture document

- **@shortcut-implement-spec.md** — Implement from an existing spec

- **@shortcut-precommit-process.md** — Run pre-commit checks

- **@shortcut-commit-code.md** — Prepare commit message

- **@shortcut-create-pr.md** — Create a pull request

And for setting up tools, reference setup docs:

- **@github-cli-setup.md** — Install and configure the GitHub CLI for PR workflows

- **@beads-setup.md** — Set up the beads issue tracker

## CLI Workflows

The CLI workflow is really just a convenience to copy and update docs.
It is helpful in three use cases currently:

- **Initialization:** The first task is to set up initial docs into your repo.
  The `speculate init` command copies all general docs as Markdown docs into a
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

- **Uninstallation:** If you want to remove Speculate’s tool configurations (but keep
  your docs), run `speculate uninstall`. This removes the Speculate header from
  `CLAUDE.md` and `AGENTS.md` (preserving any other content you’ve added), removes the
  `.cursor/rules/` symlinks, and removes **`.speculate/settings.yml`**. It does *not*
  remove the `docs/` directory or **`.speculate/copier-answers.yml`** (so you can still
  run `speculate update` later if desired).

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

1. You install the CLI and run `speculate init` from within your repo.
   This copies a bunch of docs into a `docs/` folder.
   (You only do this once but you can also run `speculate update` in the future if you
   want to update docs after the Speculate repo changes.)

2. You want to add a new feature or perform a task like a refactor.
   The first step is to plan it.
   Reference
   **[shortcut-new-plan-spec.md](docs/general/agent-shortcuts/shortcut-new-plan-spec.md)**
   (just hit `@` and type `new-plan` and it’s generally sufficient) and give your agent
   of choice (Claude Code, Codex, or Cursor) an initial description of what you want.
   The agent will read this shortcut doc, follow the listed steps to find the plan spec
   template doc, and fill it in a plan using the information you’ve given.
   You can review and iterate on the spec.
   Because of the shortcut instructions it will be placed at
   **`docs/project/specs/active/plan-YYYY-MM-DD-some-feature.md`**. Keep chatting and
   reviewing the plan until the it looks like it is a reasonable background, motivation,
   and general architecture changes.

3. Typically you’d then do a more detailed implementation plan that pulls in more code
   for context and maps out what parts of the codebase need to change.
   Reference
   **[shortcut-new-implementation-spec.md](docs/general/agent-shortcuts/shortcut-new-implementation-spec.md)**
   and the agent then copies the implementation spec template and fills that in based on
   what’s been done in the planning spec.

4. Once the plan and implementation specs are ready.
   Reference
   **[shortcut-implement-spec.md](docs/general/agent-shortcuts/shortcut-implement-spec.md)**
   with the spec in context, and it will then begin implementation.

5. Say during this process you notice you’ve made some poor architecture choices because
   you didn’t research available libraries or fully reference the right parts of the
   codebase well enough in the implementation plan.
   It’s time to do more research and analysis.
   You reference
   **[shortcut-new-research-brief.md](docs/general/agent-shortcuts/shortcut-new-research-brief.md)**
   and tell it to research all available alternative libraries and save the research
   brief. Iterate on this doc until satisfied.
   Make sure it has good links and background.

6. Now you have an idea of what library to use but are not sure of how many places in
   the codebase need to change.
   Your codebase has gotten quite large and it’s getting confusing, so you tell the
   agent to write a full architecture summary by referencing
   **[shortcut-new-architecture-doc.md](docs/general/agent-shortcuts/shortcut-new-architecture-doc.md)**.
   The agent looks through the codebase and you iterate to improve the architecture doc.

7. Now return to your plan spec, reference them, and tell the agent to reference both
   the research brief and the architecture doc, and revise the plan spec, including the
   architecture doc as background.
   Reference
   **[shortcut-implement-spec.md](docs/general/agent-shortcuts/shortcut-implement-spec.md)**.

8. Repeat with the implementation plan spec.
   Now we are ready to try implementing again.
   As you go, you want the agent to do more testing.
   Reference rules docs like
   **[general-tdd-guidelines.md](docs/general/agent-guidelines/general-tdd-guidelines.md)**
   and tell it to be stricter about test-driven development.

9. Finally you’re at an initial stopping point and tests are passing.
   Reference
   **[shortcut-commit-code.md](docs/general/agent-shortcuts/shortcut-commit-code.md)**
   to commit. These instructions tell the agent to

   - Run all linting and tests and fix everything

   - Review code and make sure it complies with relevant coding rules

   - Run all tests again after review edits

   - Backfill the specs so we know they are in sync with the code that is committed

   - Commit the code (fixing any commit hooks if something slipped through)

10. Repeat the processes above until the feature is getting complete.
    Reference
    **[shortcut-new-validation-spec.md](docs/general/agent-shortcuts/shortcut-new-validation-spec.md)**
    to have it write a spec of what automated testing has been done and what needs to be
    manually validated by you.

11. Reference
    **[shortcut-create-pr.md](docs/general/agent-shortcuts/shortcut-create-pr.md)** to
    request the agent do a final review of all code on your branch and use `gh` to file
    a PR that references the relevant parts of the validation spec.
    You can now review the PR again, do manual testing, repeat the above steps as
    desired.

12. During this whole process, you can add more agent rules, research docs, template
    improvements, etc. Agent coding is best when you iteratively improve processes all
    the time!

13. Finally, you can run `speculate update` to get updates to the shared general
    structure in this repo.
    Conflicts are detected and you can deal with merges.

That’s a bit complex.
But it is also quite powerful.
By now I hope you see how all these docs work together in a structure to make agent
coding quite fast *and* the quality of code higher.

## Installing to Claude Code, Codex, and Cursor

The `speculate init` command automatically configures all three tools:

- **CLAUDE.md** (`CLAUDE.md`) — Adds a header pointing to the docs (preserves any
  existing content)

- **AGENTS.md** (`AGENTS.md`) — Same header for Codex compatibility

- **.cursor/rules/** — Creates symlinks to **`docs/general/agent-rules/*.md`**

This setup is idempotent—running `init` or `install` multiple times is safe and won’t
overwrite your customizations to `CLAUDE.md` or `AGENTS.md`.

The source of truth for all rules is
[`docs/general/agent-rules/`](docs/general/agent-rules/).

### Manual Setup (optional)

If you prefer to configure manually instead of using `speculate init`, create
`CLAUDE.md` and/or `AGENTS.md` referencing the docs:

```markdown
Read @docs/docs-overview.md first for project documentation.
Follow rules in @docs/general/agent-rules/.
```

For Cursor, run `speculate install` to create the `.cursor/rules/` symlinks (Cursor
requires `.mdc` extension which the CLI handles automatically).

### Automatic Workflow Activation

The
**[`automatic-shortcut-triggers.md`](docs/general/agent-rules/automatic-shortcut-triggers.md)**
(**`automatic-shortcut-triggers.md`**) rule enables automatic shortcut triggering.
When an agent receives a request, it checks the trigger table and uses the appropriate
shortcut from **`docs/general/agent-shortcuts/`**.

For example:

- “Create a plan for user profiles” → triggers **@shortcut-new-plan-spec.md**

- “Commit my changes” → triggers **@shortcut-precommit-process.md** →
  **@shortcut-commit-code.md**

You can also invoke shortcuts explicitly by referencing them (e.g., typing `@` and
selecting **`shortcut-new-plan-spec.md`**).

## Feedback?

Would like to get feedback on how this works for you and suggestions for improving it!
My info is on [my profile](https://github.com/jlevy).
Posts or DMs on Twitter are easiest.
