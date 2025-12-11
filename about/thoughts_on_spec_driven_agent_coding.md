## Thoughts on Spec-Driven Agent Coding

Joshua Levy

2025-12-10

### Can Agents Write Most of Your Code?

I’ve read and written a lot of code over the past 20 years, mostly in startups.
Over the past couple years I’ve been heavily using LLMs for coding.
But until summer 2025, I did it very interactively, usually in Cursor, writing key parts
myself, then LLMs to edit and debug, touching the code at almost every stage.

However, then I began working with a friend on a new but complex full-stack product,
[AI Trade Arena](https://www.aitradearena.com/). This had a lot of product surface area.
So we began to experiment with using Claude Code and Cursor agents aggressively to write
more and more of the code.
A greenfield project with a modern framework (this is a full-stack agent framework and
web UI in TypeScript with a [Convex](https://github.com/get-convex) backend) and only 2
(human) developers was a good testbed for new development processes.

Unlike quick vibe coding projects, we wanted this to be a maintainable product.
At first, unsurprisingly, as the codebase grew, we saw lots of slop code and painfully
stupid bugs. This really isn’t surprising: by now we all realize the training data for
LLMs includes mostly mediocre code.
Even worse, just like with human engineers, if you let an agent ship poor code, that one
bad bit of code encourages the next agent to repeat the problem.
Even the best agents using modern models like Claude Sonnet 4.5 and GPT-5 Codex High
make *really* stupid (and worse, subtle) errors.

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
  These reference the long-lived docs for additinal context.

The workflows around all the docs a bit complex.
But *agents have much higher tolerance for process rules than human engineers*. They are
so cheap, process is worth it!

It’s exactly these rules and processes that give significant improvements in both speed
and code quality. The codebase grew quickly, but the more good structure we added, the
more maintainable it became.

### What Worked

After about a month of this, we didn’t wince as often because the code quality was so
low, even when the code was entirely agent-written.
Refactors were also easier because we had good architecture docs.

In about two months, we shipped about 250K lines of full-stack TypeScript code (with
Convex as a backend) and about 250K lines of Markdown docs.
Over 95% of the actual code was agent written, but with varying amounts of iterative
human feedback. About 90% of specs, architecture docs, and research briefs were agent
written but with much more human feedback and often requests for very specific changes
or deleting whole chunks spec that were poorly conceived by an agent.
But only about 10% of agent rules are edited by agents.

However only about 10% of our agent rules are hand written.
It’s critical that general rules be carefully considered.
For example, optional arguments in TypeScript were so error prone for agent refactors,
we actually just ban the agent from using it and insist on explicit nullable arguments.

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

### Advantages of Spec-Driven Coding

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

### More Conclusionss

A few more thoughts on all this:

1. Agent coding is changing ridiculously quickly and it has improved a lot just since
   mid-2025. But none of this is foolproof.
   The agent can write

2. Spec-driven development like this is powerful but most effective if you’re a fairly
   senior engineer already and can aggressively correct the agent during spec writing
   and when reviewing code.

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

## About Beads (New!)

A big recent development has been the popularity of Steve Yegge’s
[beads tool](https://github.com/steveyegge/beads).

One of his big insights is that beads are like light-weight, token-friendly issues,
replacing Markdown checklists and to-do lists that are often error prone.

Beads are indeed awesome.
I think they are the best tool yet for agent task management, progress tracking, and
task orchestration.

He also talks about how plan docs become overwhelming after while, so uses beads to
replace them.
At least based on my initial experience with beads, I still find the larger
spec-driven process outlined above still is essential, but beads relieve the pressure on
using Markdown for tracking tasks and progress.
In particular, long-lived docs like the architecture and research docs seem only to help
with beads, so you don’t have to rewrite such context over and over.

I’ve started integrating beads into the existing spec workflows to track all
implementation work and it seems to complement the other docs it pretty well so far.
(I’ve only been doing this for a few days so will update this soon.)
