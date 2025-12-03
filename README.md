# Speculate

**Speculate** is a **project structure for spec-driven agent coding**.

It includes **common rules, templates, and shortcut prompts** (in the [docs/](docs/)
folder) that help any coding agent like Claude Code, Codex, or Cursor plan better using
specs, follow more defined processes that result in better code.
You can browse these in the [docs/](docs/) folder.

Speculate also includes a **CLI tool**, `speculate`, that helps copy and update these
Markdown docs within your own repo.

The goal of this structure is to improve development *and* quality of code.

You can use these docs however you like, but we find it is the combination of workflows
that really adds benefit.
It is likely a good fit for individual senior engineers or small teams who want the
velocity of writing lots of code with agents but still need sustainable, good
engineering that won’t fall apart as a codebase grows in complexity.

## Quick Start

1. **Install the CLI**:

   Use [uv](https://docs.astral.sh/uv/):

   ```bash
   uv tool install speculate-cli
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

   Before pointing agents at your repo, make sure `docs/development.md` holds your key
   developer workflow docs.
   You may already have this, or see
   [`docs/development.npm.sample.md`](docs/development.npm.sample.md) for an example.
   Agents read this file first to understand how to build and test your project.

4. **Start using shortcuts:**

   Reference `@shortcut:new-plan-spec.md` to plan a feature,
   `shortcut:new-implementation-spec.md` to design the implementation, then
   `@shortcut:implement-spec.md` to implement, `@shortcut:commit-code.md` to commit.

## Background

### Can Agents Write Most of the Code?

I’ve read and written a lot of code over the past 20 years, mostly in startups.
Over the past couple years I’ve been heavily using LLMs for coding.
But until summer 2025, I did it very interactively, usually in Cursor, writing key parts
myself, then LLMs to edit and debug, touching the code at almost every stage.

However, then I began working with a friend on a new but complex full-stack product.
We had a lot to build, so we began to experiment with using Claude Code and Cursor
agents aggressively to write more and more of the code.

At first, unsurprisingly, as the codebase grew, we saw lots of slop code and painfully
stupid bugs. This really isn’t surprising: the training data for LLMs includes mostly
mediocre code. Even worse, just like with human engineers, if you let an agent ship poor
code, that one bad bit of code encourages the next agent to repeat the problem.

### Common Agent Problems

Without good examples and careful prompting, even the best agents perpetuate terrible
patterns and rapidly proliferate unnecessary complexity.
For example, agents will routinely

- Make a conspicuously poor decision (like parsing YAML with regular expressions) then
  double down on it over and over

- Blindly confirm erroneous assumptions or statements you make (“you’re absolutely
  right!”) even if official docs or tests or code clearly show they are false

- Create new TypeScript types over and over that nearly duplicate other types

- Choose poor libraries or out of date versions of libraries

- Forget important testing steps or not write tests at all

- Stop commenting or documenting code effectively then repeat the poor patterns until
  there is no effective documentation of the purpose of files or key types or functions

- Write trivial and useless test clutter (including provably trivial tests, like
  creating an object with a certain value and checking its fields didn’t mysteriously
  change)

- Use lots of optional parameters then refactor and accidentally omit those parameters,
  creating subtle bugs not caught by the type checker

- Design code without any good agent-friendly testing loops, like using complex database
  queries that can only be tested via a React web interface (they just tell you it’s
  “production ready” and suggest that *you* test it!)

- Preserve backward compatibility needlessly (like every time they rename a method!)
  but then forget it in others (like subtle schema changes)

- Compound one poor design choice on top of another repeatedly, until it’s a Rube
  Goldberg machine where the whole design needs to be simplified immensely

- Make fundamental incorrect assumptions about a problem if you have not been
  sufficiently explicit (and unless prompted, not check with you about it)

- Invent features that don’t exist in tools and libraries, wasting large amounts of time
  before discovering the error

- Re-invent the same Tailwind UI patterns and stylings over and over with random and
  subtle variations

### Enforcing Process and Quality

But we used all these problems as a chance to get more disciplined and improve
processes—much like you would with a human engineering team.

The first area of improvement was **more rigorous development processes**. We moved most
coding to specification-driven development.
We broke specs into planning, implementation, and validation stages for more precision.
We enforced strict coding rules at commit time to reduce common bugs we saw agents
introduce.

And we added tests. Lots and lots of tests: unit tests, integration tests, golden tests,
and end-to-end tests.

The second way was **more flexible context engineering**. In practice, this really means
lots of docs organized by workflow purpose.
You have longer-lived research docs with background, architecture docs summarizing the
system, several kinds of specs for planning, implementation, and validation, and
shortcut docs that define process.

The workflows are fairly complex.
But it’s exactly these rules and processes that give significant improvements in both
speed and code quality.
The codebase grew quickly, but the more good structure we added, the more maintainable
it became.

### What Worked

After about a month of this, we didn’t wince when looking at agent code anymore.
Refactors were also easier because we had good architecture docs.
In about two months, we shipped about 250K lines of full-stack TypeScript code (with
Convex as a backend) and about 250K lines of Markdown docs.

For truly algorithmic problems, architecture and infrastructure design, and machine
learning engineering, it seems like deeper human involvement is still essential.
Agents are just too prone to large mistakes a junior engineer might miss.
But for much routine product engineering, we feel most of the agent code is on a par or
better than the engineering quality we’ve seen in other startup teams.

You can still read the agent code about as well as code written by good human engineers.
And decisions and architecture is documented *better* than by most human engineering
teams.

In short, aggressive use of agent coding can go very poorly or very well, depending on
the kind of engineering, the process, and the engineering experience of the team.
We are still evolving it, but we have found this agent coding structure extremely
helpful for certain kinds of development.
It likely works best for very small teams of senior engineers working on feature-rich
products. But parts of this process can likely be adapted to other situations too.

## Advantages of Spec-Driven Coding

It’s worth talking a little why specs are so important for agents.
With a good enough model and agent, shouldn’t it be able to just write the code based on
a user request? Often, no!
Specs have key advantages because they:

- **Enforce a thinking process on the agent:** LLMs do much, much better if forced to
  think step by step.

- **Enforce a thinking process for the human:** Writing a spec forces the user to think
  through ambiguities or assumptions earlier, before the agent gets too far wasting time
  on implementing something that won’t work as intended.

- **Manage context for the agent:** This helps the agent have only the relevant
  information from the codebase in context at a given time.
  Specs can also easily be reviewed efficiently by a second or third model!
  (This is a big advantage!)

- **Manage context for the human:** If written well, specs are more efficient at
  allowing a senior engineer to review and correct decisions at a higher level of
  abstraction. (As a side note, this is why good agent coding is much easier for senior
  engineers than junior engineers.)

- **Share context:** Since the spec is shared, as multiple human developers work
  together and with agents, more shared context in docs allows all people and tools to
  look at the same things first.

- **Enforce consistency in development tasks:** By breaking the development process into
  research, planning, architecture, implementation, and validation phases, it allows
  greater consistency at avoiding common mistakes.

- **Allow consolidation of internal and external references**. Specs should always have
  copious citations and links to the codebase.
  This lets an agent gain context but then go deeper where needed.
  And it is key to avoiding many of the problems where agents re-invent the wheel
  repeatedly because they are unaware of better approaches.

## About Organizing Specs and Docs

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

- Organize docs into types *by lifecycle*: Most specs are short-lived only during
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

## Documentation Layout

### Key Docs

- **[`docs/docs-overview.md`](docs/docs-overview.md)** is a high-level roadmap of every
  rule, shortcut, and spec.
  The general agent rules should always point to this first.

- **`docs/development.md`** is your concise project-specific setup.
  It should cover your key developer workflows to format, lint, test, and release.
  A sample ([`docs/development.npm.sample.md`](docs/development.npm.sample.md)) ships in
  the repo; copy or rewrite it as `docs/development.md` and keep it current so agents
  know how to build and validate the project.

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
│   ├── agent-shortcuts/        # Task prompts (shortcut:*.md)
│   │   ├── shortcut:new-plan-spec.md
│   │   ├── shortcut:implement-spec.md
│   │   ├── shortcut:commit-code.md
│   │   └── ...
│   └── agent-guidelines/       # Longer guidance docs (TDD, DI, testing)
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
    (`plan-YYYY-MM-DD-*.md`, `impl-YYYY-MM-DD-*.md`, `valid-YYYY-MM-DD-*.md`).

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

You can reference any of these docs as needed in chat.
The most common pattern is simply to mention the shortcut docs.
For example, the key ones are:

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

3. Typically you’d then do a more detailed implementation plan that pulls in more code
   for context and maps out what parts of the codebase need to change.
   Reference
   [shortcut:new-implementation-spec.md](docs/general/agent-shortcuts/shortcut:new-implementation-spec.md)
   and the agent then copies the implementation spec template and fills that in based on
   what’s been done in the planning spec.

4. Once the plan and implementation specs are ready.
   Reference
   [shortcut:implement-spec.md](docs/general/agent-shortcuts/shortcut:implement-spec.md)
   with the spec in context, and it will then begin implementation.

5. Say during this process you notice you’ve made some poor architecture choices because
   you didn’t research available libraries or fully reference the right parts of the
   codebase well enough in the implementation plan.
   It’s time to do more research and analysis.
   You reference
   [shortcut:new-research-brief.md](docs/general/agent-shortcuts/shortcut:new-research-brief.md)
   and tell it to research all available alternative libraries and save the research
   brief. Iterate on this doc until satisfied.
   Make sure it has good links and background.

6. Now you have an idea of what library to use but are not sure of how many places in
   the codebase need to change.
   Your codebase has gotten quite large and it’s getting confusing, so you tell the
   agent to write a full architecture summary by referencing
   [shortcut:new-architecture-doc.md](docs/general/agent-shortcuts/shortcut:new-architecture-doc.md).
   The agent looks through the codebase and you iterate to improve the architecture doc.

7. Now return to your plan spec, reference them, and tell the agent to reference both
   the research brief and the architecture doc, and revise the plan spec, including the
   architecture doc as background.
   Reference
   [shortcut:implement-spec.md](docs/general/agent-shortcuts/shortcut:implement-spec.md).

8. Repeat with the implementation plan spec.
   Now we are ready to try implementing again.
   As you go, you want the agent to do more testing.
   Reference rules docs like
   [general-tdd-guidelines.md](docs/general/agent-guidelines/general-tdd-guidelines.md)
   and tell it to be stricter about test-driven development.

9. Finally you’re at an initial stopping point and tests are passing.
   Reference
   [shortcut:commit-code.md](docs/general/agent-shortcuts/shortcut:commit-code.md) to
   commit. These instructions tell the agent to

   - Run all linting and tests and fix everything

   - Review code and make sure it complies with relevant coding rules

   - Run all tests again after review edits

   - Backfill the specs so we know they are in sync with the code that is committed

   - Commit the code (fixing any commit hooks if something slipped through)

10. Repeat the processes above until the feature is getting complete.
    Reference
    [shortcut:new-validation-spec.md](docs/general/agent-shortcuts/shortcut:new-validation-spec.md)
    to have it write a spec of what automated testing has been done and what needs to be
    manually validated by you.

11. Reference
    [shortcut:create-pr.md](docs/general/agent-shortcuts/shortcut:create-pr.md) to
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

## More Take-Aways

After using this structure heavily for the past 2-3 months as well as using coding tools
in other ways for the past 2 years, we do have some take-aways:

1. Agent coding is changing ridiculously quickly and it has improved a lot just since
   mid-2025. But none of this is foolproof.
   Even the best agents like Claude Sonnet 4.5 and GPT-5 Codex High make really stupid
   errors sometimes.

2. Spec-driven development like this is most effective if you’re a fairly senior
   engineer already and can aggressively correct the agent during spec writing and when
   reviewing code.

3. It is also most effective for full-stack or product engineering, where the main
   challenge is implementing everything in a flexible way.
   Visually intensive frontend engineering and “harder” algorithmic, infrastructure, or
   machine learning engineering still seem better suited to iteratively writing code by
   hand.

4. Even if you are writing code by hand, the processes for writing research briefs and
   architecture docs is still useful.
   Agents are great at maintaining docs!

5. For product engineering, you can often get away with writing very little code
   manually if the spec docs are reviewed.
   With good templates and examples, you can chat with the agent to write the specs as
   well. But you do have to actually read the spec docs and review the code!

6. But with some discipline this approach is really powerful.
   Contrary to what some say, we have found it doesn’t lead to buggy, dangerous, and
   unmaintainable code the way blindly vibe coding does.
   And it is much faster than writing the same code fully by hand.

7. Avoid testing cycles that are manual!
   It’s best to combine this approach with an architecture that makes testing really
   easy. If at all possible, insist on architectures where all tasks are easy to run from
   the command line. Insist on mockable APIs and databases, so even integration testing
   is easy from the command line.

## Installing to Claude Code, Codex, and Cursor

The source of truth for all rules is `docs/general/agent-rules/`. After running
`speculate init`, configure your agent tool to load these rules.

### Cursor Setup

Create symlinks (or copies) from `.cursor/rules/` to the agent-rules docs:

```bash
mkdir -p .cursor/rules
cd .cursor/rules
ln -s ../../docs/general/agent-rules/*.md .
```

### Claude Code and Codex Setup

Create root-level `CLAUDE.md` and/or `AGENTS.md` files that reference the docs.
Example `CLAUDE.md`:

```markdown
Read @docs/docs-overview.md first for project documentation.
Follow rules in @docs/general/agent-rules/.
```

### Automatic Workflow Activation

The
[`automatic-shortcut-triggers.md`](docs/general/agent-rules/automatic-shortcut-triggers.md)
rule enables automatic shortcut triggering.
When an agent receives a request, it checks the trigger table and uses the appropriate
shortcut from `docs/general/agent-shortcuts/`.

For example:

- “Create a plan for user profiles” → triggers @shortcut:new-plan-spec.md

- “Commit my changes” → triggers @shortcut:precommit-process.md →
  @shortcut:commit-code.md

You can also invoke shortcuts explicitly by referencing them (e.g., typing `@` and
selecting `shortcut:new-plan-spec.md`).

## Feedback?

Would like to get feedback on how this works for you and suggestions for improving it!
My info is on [my profile](https://github.com/jlevy).
Posts or DMs on Twitter are easiest.
