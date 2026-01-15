# Lessons from 500K Lines of Spec-Driven Agent Coding

Joshua Levy ▪ 2025-12-11

👉 *You can try this out on your own project!
The **[speculate](https://github.com/jlevy/speculate)** repo has all the prompts and
templates discussed below and a CLI to copy them into your repo.
You can also see [these slides](speculate_slides.html) from a talk I gave about this.*

## Can Agents Write a Complex Production Application?

Recently, I’ve been doing a *lot* of agent coding.
I’d like share some learnings after building a fairly complex product that is almost
entirely agent coded.
The experience has significantly changed how I now code with LLMs and evolved my views
on what it means to be a software engineer in 2026.

It’s a fairly complex full-stack web app,
[AI Trade Arena](https://www.aitradearena.com/), which we launched last week and was
[#1 on HN](https://news.ycombinator.com/item?id=46154491) for the day.
It was built with two developers ([Kam](https://x.com/kamleung911) and
[me](https://x.com/ojoshe)) with about 250K lines of TypeScript and 250K lines of
Markdown docs. It is about 95% agent-written code and 90% agent-written specs.

The process has involved some painful experimentation, quite a few (at least to me)
non-obvious tricks, and a few new mental models for coding.
This post and prompt repository are an attempt to share them with you.

## About Me

I’m a longtime startup engineer and founder.
Over the past couple years, I’ve been heavily using LLMs for coding.
But until around September 2025, I did it very interactively, usually in Cursor, writing
key parts myself, then using LLMs to fill in parts and to debug.
I’m a picky code reviewer so I usually ended up touching the code at almost every stage.

## About the Codebase

As a greenfield effort, this was a good opportunity to try new development processes.
We wanted agents to do as much as possible.
But unlike a vibe-coded hackathon project, we wanted this to be a maintainable codebase
we could use and maintain as a real product.
It’s a full-stack web app with a React web UI and a backend agent framework with
[Convex](https://github.com/get-convex) for the backend.[^1]

## The Problem of Slop Code

With LLMs, “slop” is not so much a description of low-quality content as it is a natural
law, like entropy in physics or the force of gravity.

Objects tend to fall to earth unless you engineer ways to prevent that.
Coding agents trend toward the center of gravity of their coding training data unless
you build structures to guide them in other directions.

Unsurprisingly, as we began using Claude Code and Cursor agents aggressively to write
nearly all of the code, we saw lots of slop: numerous poor stylistic choices that
wrapped more serious design mistakes, regularly punctuated with painfully stupid bugs.
To add insult to injury, LLMs vacillate between assuring you’re right and denying things
are problems.

And worse, slop doesn’t just grow; it accelerates.
Just like with human engineers, if you let an agent ship poor code, that one bad bit of
code encourages the *next* agent to repeat the same questionable style or bad judgement.
Even the best agents using modern models like Claude Sonnet 4.5 and GPT-5 Codex High can
make *really* stupid (and worse, subtle) errors.

Good code means pushing away from the average—toward clarity, simplicity, and
flexibility in solving a problem.
Without good examples and careful prompting, even the best agents perpetuate terrible
patterns and proliferate unnecessary complexity.

For example, we saw agents routinely:

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

## Enforcing Process and Quality

We used all these problems as a chance to get more disciplined and improve
processes—much like you would with a human engineering team.

The first area of improvement was **more rigorous development processes**. We moved most
coding to specification-driven development:

- We broke specs into planning, implementation, and validation stages for more
  precision.

- We enforced strict coding rules at commit time to reduce common bugs we saw agents
  introduce.

- We added another layer of shortcuts: small docs that outline a process.
  It’s then quick to reference shortcuts.

- And we added tests. Lots and lots of tests: unit tests, integration tests, golden
  tests, and end-to-end tests.

The second way was **more flexible context engineering**. In practice, this really means
lots of docs organized by the purpose or workflow:

- **Long-lived docs:** These are research docs with background and architecture docs
  summarizing the system.
  It also includes the shortcut docs with defined processes.

- **Shorter-lived specs:** Specs are docs used to refine a specific larger effort like a
  feature, complex bugfix, or a refactor.
  Specs can be used for planning, implementation, and validation.
  These reference the long-lived docs for additional context.

The workflows around all the docs are a bit complex.
But *agents have much higher tolerance for process rules than human engineers*. They are
so cheap, process is worth it!

It’s exactly these rules and processes that give significant improvements in both speed
and code quality. The codebase grew quickly, but the more good structure we added, the
more maintainable it became.

## What Worked

After about few weeks of this, we didn’t wince as often because the code quality
improved, even when the code was entirely agent-written.
Refactors were also easier because we had good architecture docs.

In two months, we shipped about **250K lines** of full-stack TypeScript code and about
**250K lines** of Markdown docs of many kinds:

- About **95% of the code** was agent written, but with varying amounts of iterative
  human feedback.

- About **90% of specs**, architecture docs, and research briefs were agent written as
  well. But these with much more human feedback and often requests for very specific
  changes or deleting whole chunks of spec that were poorly conceived by an agent.

- However, only **about 10% of agent rules** and process docs were agent written.
  It’s critical that general rules be carefully considered.
  For example, optional arguments in TypeScript were so error prone for agent refactors,
  we actually just ban the agent from using it and insist on explicit nullable
  arguments.

- If you count transient docs as well as long-lived docs, we find we usually had in
  total about as much docs as code.
  But if you ignore transient docs like completed specs, it’s more like **25% long-lived
  docs and 75% code**.

For truly algorithmic problems, architecture and infrastructure design, and machine
learning engineering, it seems like deeper human involvement is still essential.
Agents are just too prone to large mistakes a junior engineer might miss.
But for much routine product engineering, we feel most of the agent code is on a par or
better than the engineering quality we’ve seen in other startup teams.

You can still read the agent code about as well as code written by good human engineers.
And decisions and architecture are documented *better* than by most human engineering
teams.

In short, aggressive use of agent coding can go very poorly or very well, depending on
the kind of engineering, the process, and the engineering experience of the team.
We are still evolving it, but we have found this agent coding structure extremely
helpful for certain kinds of development.
It likely works best for very small teams of senior engineers working on feature-rich
products. But parts of this process can likely be adapted to other situations too.

## Advantages of Spec-Driven Coding

It’s worth talking a little about why specs are so important for agents.
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

- **Allow consolidation of internal and external references:** Specs should always have
  copious citations and links to the codebase.
  This lets an agent gain context but then go deeper where needed.
  And it is key to avoiding many of the problems where agents re-invent the wheel
  repeatedly because they are unaware of better approaches.

## About Organizing Specs and Docs

The [speculate](https://github.com/jlevy/speculate) repo is largely just a bunch of
Markdown docs in a clean, organized structure that you can add to and adjust.

We try to keep all docs small to medium sized, for better context management.
If you like, just go read the [docs/](https://github.com/jlevy/speculate/tree/main/docs)
files and you’ll see how it works.

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

## About Beads (New!)

A significant recent development has been the popularity of Steve Yegge’s
[beads tool](https://github.com/steveyegge/beads).

His big insight with beads is that we need light-weight, token-friendly issue tracking,
replacing Markdown checklists and to-do lists that are often error prone for agents.

Beads are indeed awesome.
I think they are the best tool yet for agent task management, progress tracking, and
task orchestration.

He also talks about how plan docs become overwhelming after a while, so uses beads to
replace them.
At least based on my initial experience with beads, I still find the larger
spec-driven process outlined above still is essential, but beads relieve the pressure on
using Markdown for tracking tasks and progress.
In particular, long-lived docs like the architecture and research docs seem only to help
with beads, so you don’t have to rewrite such context over and over.

I’ve started integrating beads into the existing spec workflows to track all
implementation work and it seems to complement the other docs it pretty well so far.
(I’ve only been doing this for a few days so will update this soon.)

## File Layout and Example Docs

Below are snapshots of how I currently lay out the docs in the project, along with
examples of (1) general rules (in this case TDD guidelines), (2) a research brief, and
(3) a more complex plan spec.

### Overall Docs Structure

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

### General Docs: Rules Example

<p align="center">
<a href="images/cursor_docs_general_rules.png"><img src="images/cursor_docs_general_rules.png" width="750" alt="General docs example"></a>
</p>

### Project Docs: Research Brief Example

<p align="center">
<a href="images/cursor_docs_project_research.png"><img src="images/cursor_docs_project_research.png" width="750" alt="Project research doc example"></a>
</p>

### Project Docs: Spec Example

<p align="center">
<a href="images/cursor_docs_project_specs.png"><img src="images/cursor_docs_project_specs.png" width="750" alt="Project spec example"></a>
</p>

## More Take-Aways

A few more thoughts on all this:

1. **Process discipline pays off:** If done carefully, spec-driven agent development is
   really powerful. Contrary to what some say, we have found it doesn’t lead to buggy,
   dangerous, and unmaintainable code the way casually vibe coding does.
   And it is much faster than writing the same code fully by hand.

2. **Check everything:** Agent coding is changing ridiculously quickly and it has
   improved a lot just since mid-2025. But none of this is foolproof.
   You always need to review the code and/or have compelling, thorough approaches to
   testing behavior.

3. **Good engineering judgement is essential:** Spec-driven development like this is
   powerful but most effective if you’re a fairly senior engineer already and can
   aggressively correct the agent during spec writing and when reviewing code.
   Don’t just let agents do the standard, common thing typical in average code.
   It really pays to think creatively about how to design something to minimize
   complexity and improve visibility and testability.

4. **Spec-driven development works well for product features:** It is also most
   effective for full-stack or product engineering, where the main challenge is
   implementing everything in a flexible way.
   Visually intensive frontend engineering and “harder” algorithmic, infrastructure, or
   machine learning engineering still seem better suited to iteratively writing code by
   hand.

5. **Agent-written docs are still useful even if you code without agents:** Even if you
   are writing code by hand, the processes for writing research briefs and architecture
   docs is still useful.
   Agents are great at maintaining docs!

6. **Design away testing cycles that are manual!** I think this point is underrated.
   Everything we’ve talked about works *far* better if you define an architecture that
   makes deep testing really easy and friendly for agents, ideally directly from the
   command line so it is “token friendly” and allows most of the code paths to be tested
   without UI testing.

## Claude Code and Other Agent Tips

Years ago, before cloud infrastructure matured, it was common as a software engineer to
spend lots of time on Linux system administration details.
You had to sort out quirks in firewall rules on a particular operating system version
just to get a web server running.

I feel like the current state of agentic coding is a lot like this.
You have to sort out lots of little setup details that are accidental to the current
agentic tooling.

Here are a few of the tips/tricks I currently use with Claude Code:

1. The ***VSCode extension for Claude Code** is probably the best UI for agent loops
   currently if you are using VSCode or Cursor.
   It is more comfortable inside the IDE than the terminal interfaces and is implemented
   efficiently. The UI is snappy.
   For Claude, it’s currently the best.

2. **Cursor’s agent loops** are quite good, and offer great features at switching models
   during a session. They’ve also added a chooser to let you ask a question to more than
   one model at once.

3. **Opus 4.5** seems like the current king of coding models.
   Great for planning and writing specs and for implementation.
   And it works great in Claude Code.
   But after you write a spec, have the other best models, especially **GPT 5.1 Codex
   Max** and **Gemini 3 Pro** review it.
   Ask to find omissions, errors, ways to simplify or improve, and they each almost
   always will find things Opus missed.
   I do this by switching out of Claude Code and using them as agents in Cursor.

4. The **Claude Code web** agent coding seems like the best way to have many agents you
   are interacting with simultaneously and managing at once across branches.
   I’ve also tried [Conductor](https://github.com/ryanmac/code-conductor) and
   [cmux](https://github.com/manaflow-ai/cmux), but at the moment Claude Code web seems
   easiest to me as a first tool, then I fall back to others for additional review or
   special uses. You can also access it from the mobile app!
   I can start an agent job at home when I wake up and monitor 20 minutes later (“yes,
   keep going!”) while I’m on the train to work.

5. However, Claude Code web has some annoying restrictions.
   The first is that it assumes you will create the PR by pressing a button to create it
   manually. This is silly.
   **Set up Claude Code Web to use the the `gh` CLI** to create the PR for you!
   That way the agent can document validation steps, test CI passes, etc.
   There is a workaround for this: use the
   [github-cli-setup.md](../docs/general/agent-setup/github-cli-setup.md) instructions
   I’ve given here.

6. Similarly, you need a custom setup to **get Claude Code Web to use beads**. See
   [beads-setup.md](../docs/general/agent-setup/beads-setup.md).

## Leveling Up Full-Stack Testing

If there’s one final point to emphasize, it’s this:

> *When agent coding, the greatest accelerator is to pick architectures and agent rules
> so the testing loop is exhaustive (high coverage), maintainable (changes easily as you
> add features), and token-friendly (updating and rerunning tests fits in a rapid
> agentic loop).*

In particular, for full-stack web development, except when absolutely necessary for UI,
testing shouldn’t require a web browser!
Three things can help with this:

- **Make everything usable via CLI:** In your design processes, insist on architectures
  where all tasks are easy to run from the command line as well as from API endpoints or
  web or mobile UIs.

- **Make everything mockable:** Insist on mockable APIs and databases, so even
  integration testing is easy from the command line and can be included in standard
  tests on every commit or PR.

- **Use golden tests:** For any workflow or operation, it should be possible to capture
  and save stable run sessions (or traces) of everything that happened in a stable,
  serialized form. Then a large portion of your end-to-end testing is token friendly and
  possible without human validation.

The use of golden tests is quite powerful and underrated.
It is far preferable to having a domain specific trace of your system’s behavior checked
into git (and diff-able with actual behavior) than to have an LLM constantly rewrite a
bunch of messy unit tests (that themselves may be buggy).

With human engineers, these policies might not always be a good idea, because they cost
extra coding time. But adding a CLI or a bunch of mocks is actually fast for an LLM! So
these are worthy investments.

As an example, here are the kinds of tests we ask agents to use in
[our TDD guidelines](https://github.com/jlevy/speculate/blob/main/docs/general/agent-guidelines/general-tdd-guidelines.md).

> Tests in the project are broken down into four types:
> 
> 1. **Unit** — fast, focused tests for small units of business logic
>    
>    - No network/web access
>
>    - Typically part of CI builds.
>
> 2. **Integration** — tests that efficiently exercise multiple components
>    
>    - Mock external APIs
>
>    - No network/web access
>
>    - Typically part of CI builds.
>
> 3. **Golden** — tests that check behavior in a fine-grained way across known “golden”
>    scenarios
>    
>    - These are an essential type of test that is often neglected but very powerful!
>      Use whenever possible.
>
>    - Work by checking input, output, and intermediate states of an execution
>
>    - All input, output, and intermediate events are saved to a serialized session file
>
>    - Events in session files are filtered to include only stable fields that don’t
>      change across runs (e.g. log timestamps are omitted)
>
>    - Expected session files are checked into codebase, should be complete but not
>      excessively long. Golden tests confirm actual session run matches expected
>      session, validating every part of the execution.
>
>    - Typically part of CI builds as long as they are fast enough.
>
> 4. **E2E** — tests of real system behavior with live APIs
>    
>    - Are not run on every commit as they can have costs or side effects or be slow.
>
>    - Require API keys and network access.

[^1]: We’ve been very happy with Convex!
    It takes a little adjustment but it is actually a great complement to agent coding.
    We recommend checking out their quite excellent
    [templates](https://github.com/get-convex/templates) to see realistic examples of
    how to use it.

