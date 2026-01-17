# Research Brief: Coding Agent Skills, Commands, and Extension Mechanisms

**Last Updated**: 2026-01-03

**Status**: Complete

**Related**:

- [automatic-shortcut-triggers.md](../agent-rules/automatic-shortcut-triggers.md)

---

## Versions Documented

| Tool/Platform | Version | Date Researched | Primary Source |
|---------------|---------|-----------------|----------------|
| Claude Code | v2.0.74 | 2026-01-03 | [CHANGELOG.md](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) |
| Claude Skills Spec | v1.0 | 2026-01-03 | [platform.claude.com](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) |
| Anthropic Skills Repo | — | 2026-01-03 | [github.com/anthropics/skills](https://github.com/anthropics/skills) |
| Superpowers | — | 2026-01-03 | [github.com/obra/superpowers](https://github.com/obra/superpowers) |
| OpenAI Codex | — | 2026-01-03 | [developers.openai.com/codex](https://developers.openai.com/codex/) |
| AGENTS.md Spec | v1.0 | 2026-01-03 | [agents.md](https://agents.md/) |
| Cursor | — | 2026-01-03 | [docs.cursor.com](https://docs.cursor.com/) |
| Windsurf (Cascade) | — | 2026-01-03 | [docs.windsurf.com](https://docs.windsurf.com/) |

*Note: "—" indicates version not explicitly published or not applicable.*

---

## Executive Summary

Modern AI coding agents (Claude Code, Cursor, OpenAI Codex, Windsurf) have converged on
similar patterns for extensibility: instruction files, reusable skills, slash commands,
and plugin systems. This research documents how each major platform implements these
mechanisms, best practices for skill authoring, and patterns for cross-platform
compatibility.

The key finding is that **skills** (model-invoked, semantic-matching instructions) and
**commands** (user-invoked explicit triggers) serve complementary roles. Platforms are
converging on a shared specification (AGENTS.md) while maintaining platform-specific
enhancements (CLAUDE.md for Claude, .cursor/rules for Cursor).

**Research Questions**:

1. How do different coding agents implement extensibility (skills, commands, rules)?
2. What are the best practices for authoring reusable agent instructions?
3. How can prompts/shortcuts be made portable across multiple agent platforms?
4. What patterns do successful skill libraries (e.g., Superpowers) use?

---

## Research Methodology

### Approach

- Documentation review of official platform docs
- Analysis of open-source skill libraries (Superpowers, anthropics/skills)
- Web research for latest updates (December 2025 - January 2026)
- Comparative analysis across platforms

### Sources

- [Claude Code Official Docs](https://code.claude.com/docs/)
- [Anthropic Skills Blog](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Anthropic Skills Repository](https://github.com/anthropics/skills)
- [Superpowers Repository](https://github.com/obra/superpowers)
- [OpenAI Codex Documentation](https://developers.openai.com/codex/)
- [AGENTS.md Specification](https://agents.md/)
- [Cursor Documentation](https://docs.cursor.com/)
- [Windsurf Documentation](https://docs.windsurf.com/)

---

## Research Findings

### 1. Claude Code Extension Mechanisms

Claude Code (v2.0.74 as of January 2026) provides the most comprehensive extension system
with four distinct mechanisms.

#### 1.1 Skills (Model-Invoked)

**Status**: ✅ Complete

Skills are markdown files that Claude **automatically invokes** based on semantic matching
of their description against user requests.

**Structure**:
```
skill-name/
├── SKILL.md           # Required: YAML frontmatter + instructions
├── reference.md       # Optional: detailed documentation
├── examples.md        # Optional: usage examples
└── scripts/           # Optional: executable utilities
    └── helper.py
```

**SKILL.md Format**:
```markdown
---
name: processing-pdfs
description: Extract text and tables from PDF files, fill forms, merge documents.
  Use when working with PDFs or when the user mentions forms or document extraction.
allowed-tools: [Read, Write, Bash]
---

# Processing PDFs

Instructions for Claude on how to process PDF files...
```

**Key Characteristics**:
- **Semantic activation**: Claude loads skills based on description matching
- **Progressive disclosure**: Only load detailed content when needed
- **Cross-platform**: Same format works in Claude.ai, Claude Code, and API
- **Tool restrictions**: Can limit which tools Claude uses via `allowed-tools`

**Locations**:
- Personal: `~/.claude/skills/`
- Project: `.claude/skills/`
- Plugin-bundled: `plugin-name/skills/`

**Source**: [Agent Skills - Claude Code Docs](https://code.claude.com/docs/en/skills)

---

#### 1.2 Slash Commands (User-Invoked)

**Status**: ✅ Complete

Commands are markdown files that users **explicitly invoke** with `/command-name`.

**Format**:
```markdown
---
description: Review code for security vulnerabilities
allowed-tools: [Read, Grep]
---

Review the following file for security issues:

@$1

Check for: SQL injection, XSS, command injection, path traversal.
```

**Features**:
- `$1`, `$2`, `$ARGUMENTS` - Positional and full argument access
- `@filename` - Include file contents
- `!bash command` - Execute shell before running prompt
- `allowed-tools` - Restrict available tools
- `model` - Override conversation model

**Locations**:
- Personal: `~/.claude/commands/`
- Project: `.claude/commands/`
- Plugin-bundled: `plugin-name/commands/` (namespaced as `/plugin:command`)

**Source**: [Slash Commands - Claude Code Docs](https://code.claude.com/docs/en/slash-commands)

---

#### 1.3 Plugins (Distribution Bundles)

**Status**: ✅ Complete

Plugins bundle commands, skills, hooks, agents, and MCP servers for distribution.

**Structure**:
```
plugin-name/
├── .claude-plugin/
│   └── plugin.json      # Manifest
├── commands/            # Slash commands
├── skills/              # Auto-triggered skills
├── hooks/               # Lifecycle handlers
├── agents/              # Subagent definitions
└── .mcp.json            # MCP server configs
```

**plugin.json**:
```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "Plugin description",
  "author": { "name": "Author" }
}
```

**Installation Methods**:
1. Marketplace: `/plugin marketplace add repo` then `/plugin install name@marketplace`
2. Direct placement: `.claude/plugins/plugin-name/`
3. Development: `--plugin-dir ./local-plugin`

**Namespacing**: Plugin commands are invoked as `/plugin-name:command-name`

**Source**: [Plugins - Claude Code Docs](https://code.claude.com/docs/en/plugins)

---

#### 1.4 CLAUDE.md (Project Instructions)

**Status**: ✅ Complete

A markdown file at the repository root that Claude reads automatically for project context.

**Purpose**:
- Project-specific coding standards
- Build/test commands
- Architecture overview
- Team conventions

**Best Practice**: Keep CLAUDE.md concise and reference detailed docs:
```markdown
IMPORTANT: Read ./docs/development.md and ./docs/architecture.md for full context.
```

---

### 2. OpenAI Codex Extension Mechanisms

OpenAI Codex uses AGENTS.md as its primary extension mechanism, now standardized under
the Linux Foundation's Agentic AI Foundation.

#### 2.1 AGENTS.md (Cascading Instructions)

**Status**: ✅ Complete

Text files that guide Codex behavior, discovered hierarchically from root to current
directory.

**Discovery Order** (per directory):
1. `AGENTS.override.md` (highest priority)
2. `AGENTS.md`
3. Configured fallbacks (e.g., `TEAM_GUIDE.md`)

**Cascading Behavior**: Instructions accumulate from repository root to current directory,
with closer files taking precedence.

**Example**:
```
/repo/
├── AGENTS.md              # Repository-wide instructions
├── packages/
│   ├── frontend/
│   │   └── AGENTS.md      # Frontend-specific instructions
│   └── backend/
│       └── AGENTS.md      # Backend-specific instructions
```

**Adoption**: The OpenAI Codex repository itself contains 88 AGENTS.md files.

**Source**: [AGENTS.md - OpenAI Codex](https://developers.openai.com/codex/guides/agents-md/)

---

#### 2.2 Codex Skills

**Status**: ✅ Complete

Codex also supports Skills with the same SKILL.md format as Claude Code.

**Key Features**:
- Available in both CLI and IDE extensions
- Same folder structure with SKILL.md
- Can include scripts and resources

**Source**: [Agent Skills - OpenAI Codex](https://developers.openai.com/codex/skills/)

---

### 3. Cursor Extension Mechanisms

Cursor uses "Cursor Rules" for project-specific AI guidance.

#### 3.1 Cursor Rules

**Status**: ✅ Complete

**Location**: `.cursor/rules/*.mdc` (or `.cursorrules` legacy)

**Format**: YAML frontmatter + Markdown content
```markdown
---
description: TypeScript Coding Standards
globs: ["*.ts", "*.tsx"]
alwaysApply: true
---

# TypeScript Rules

- Use strict TypeScript
- No `any` types
- Prefer interfaces over types
```

**Key Features**:
- `globs` - Apply rules to specific file patterns
- `alwaysApply` - Load rules into every conversation
- Symlinks supported for sharing rules across projects

**Comparison to Claude Code**:
| Feature | Cursor Rules | Claude Code Skills |
|---------|-------------|-------------------|
| Activation | `alwaysApply` or file pattern | Semantic matching |
| Format | `.mdc` files | `SKILL.md` folders |
| Location | `.cursor/rules/` | `.claude/skills/` |

---

### 4. Windsurf Extension Mechanisms

Windsurf (formerly Codeium) uses Cascade with rules and memory systems.

#### 4.1 Cascade Rules

**Status**: ✅ Complete

**Features**:
- User-defined rules for language, framework, API preferences
- Auto-generated memories from interactions
- Rulebooks with auto-generated slash commands
- Memory persistence across conversations

**Configuration**:
- Rules defined through settings UI
- `.codeiumignore` for file exclusions
- Global rules in `~/.codeium/`

**Source**: [Windsurf Cascade Documentation](https://docs.windsurf.com/windsurf/cascade/)

---

### 5. Cross-Platform Standards

#### 5.1 AGENTS.md Specification

**Status**: ✅ Complete

An emerging open standard for agent instructions, stewarded by the Agentic AI Foundation
under the Linux Foundation.

**Adopters**:
- OpenAI Codex
- Amp
- Jules (Google)
- Cursor
- Factory

**Principle**: "Think of it as a README for agents."

**Source**: [AGENTS.md Specification](https://agents.md/)

---

### 6. Superpowers: A Skill Library Case Study

Superpowers is the most comprehensive open-source skill library for Claude Code,
demonstrating production-grade patterns.

#### 6.1 Architecture

**Status**: ✅ Complete

**Directory Structure**:
```
superpowers/
├── skills/              # Core skill library
├── agents/              # Agent configurations
├── commands/            # Slash commands
├── hooks/               # Lifecycle hooks
├── lib/                 # Utilities
└── .claude-plugin/      # Plugin metadata
```

**Core Skills**:

| Category | Skills |
|----------|--------|
| Planning | `brainstorming`, `writing-plans`, `executing-plans` |
| Development | `test-driven-development`, `systematic-debugging` |
| Collaboration | `requesting-code-review`, `receiving-code-review` |
| Workflow | `dispatching-parallel-agents`, `using-git-worktrees` |
| Meta | `writing-skills`, `using-superpowers` |

#### 6.2 Key Patterns

**Mandatory Workflows**: Skills trigger automatically—"the agent checks for relevant
skills before any task."

**Structured Process**: After installation, Claude follows:
1. Receive Requirements
2. Brainstorm (Socratic refinement)
3. Create Detailed Plan
4. Write Test Cases (TDD)
5. Write Code to Pass Tests
6. Quality Check

**Token Efficiency**: Work is split into 5-minute chunks with progress written to
markdown files, preserving context across sessions.

**Installation**:
```
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

**Sources**:
- [Superpowers GitHub](https://github.com/obra/superpowers)
- [Skills for Claude - Jesse Vincent](https://blog.fsck.com/2025/10/16/skills-for-claude/)
- [Superpowers Blog Post](https://blog.fsck.com/2025/10/09/superpowers/)

---

## Comparative Analysis

### Extension Mechanism Comparison

| Platform | Instructions | Skills | Commands | Plugins |
|----------|-------------|--------|----------|---------|
| Claude Code | CLAUDE.md | ✅ SKILL.md | ✅ /command | ✅ Full plugins |
| OpenAI Codex | AGENTS.md | ✅ SKILL.md | ✅ Limited | ❌ |
| Cursor | .cursorrules | ❌ | ❌ | ❌ |
| Windsurf | Rules UI | ❌ | ✅ Rulebooks | ❌ |

### Activation Comparison

| Type | Claude Skills | Cursor Rules | Codex AGENTS.md |
|------|--------------|--------------|-----------------|
| Trigger | Semantic matching | File pattern / always | Directory hierarchy |
| Scope | Per-task | Per-file or global | Cascading |
| User control | Implicit | Explicit via globs | Explicit via location |

### Portability Assessment

**Most Portable**: AGENTS.md (cross-platform standard)

**Most Capable**: Claude Code Plugins (full bundle with skills, commands, hooks)

**Best for Teams**: Skills in `.claude/skills/` or `.cursor/rules/` (version controlled)

---

## Best Practices

### 1. Skill Authoring (Claude Code)

**Conciseness**: "The context window is a public good." Only include information Claude
doesn't already know. Challenge every token.

**Progressive Disclosure**: Keep SKILL.md under 500 lines. Split detailed content into
reference files that Claude reads only when needed.

**Specific Descriptions**: Include trigger keywords users naturally mention.
- Good: "Extract text and tables from PDF files, fill forms, merge documents"
- Bad: "Helps with documents"

**Naming Convention**: Use gerund form (verb + -ing):
- Good: `processing-pdfs`, `analyzing-spreadsheets`
- Bad: `pdf-helper`, `spreadsheet-utils`

**Source**: [Skill Authoring Best Practices - Claude Docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)

---

### 2. Cross-Platform Compatibility

**Use AGENTS.md as Base**: Create AGENTS.md for broad compatibility, then add
platform-specific enhancements.

**Symlink Strategy**: Maintain source files in a docs folder, symlink to platform
locations:
```
docs/rules/typescript.md          # Source of truth
.cursor/rules/typescript.mdc      # Symlink for Cursor
.claude/skills/typescript/SKILL.md # Adapted for Claude
```

**Shared Prefix Convention**: Use consistent naming across platforms:
```
docs/general/agent-shortcuts/shortcut:new-plan-spec.md
→ .claude/plugins/speculate/commands/new-plan-spec.md
→ .cursor/rules/new-plan-spec.mdc
```

---

### 3. Automatic Triggering

**Claude Code**: Use skills with comprehensive descriptions for semantic matching.

**Cursor**: Set `alwaysApply: true` for mandatory rules.

**Speculate Pattern**: Create a "routing skill" that maps intents to commands:
```markdown
---
name: workflow-router
description: Routes development tasks to appropriate commands
---

| User intent | Command |
|-------------|---------|
| Creating a feature plan | /speculate:new-plan-spec |
| Committing code | /speculate:precommit-process |
```

---

### 4. Token Efficiency

**From Superpowers**: Split work into checkpointed chunks, write progress to files.

**From Anthropic**: Use reference files for detailed content, keep SKILL.md lean.

**Validation Loops**: Run-validator-fix-errors-repeat cycles catch problems early.

---

## Open Research Questions

1. **Skill Marketplace Standards**: Will platforms converge on a shared skill
   distribution format?

2. **Cross-Platform Skill Translation**: Can skills be automatically converted between
   Claude Code and Cursor formats?

3. **Enterprise Skill Governance**: How should organizations manage skill libraries
   across teams?

4. **Skill Versioning**: Best practices for updating skills without breaking dependent
   workflows?

---

## Recommendations

### Summary

For maximum compatibility and capability, use a layered approach:
1. AGENTS.md for cross-platform base instructions
2. Claude Code plugins for full skill/command bundles
3. Cursor rules symlinked to shared docs
4. A CLI tool to manage installation and updates

### Recommended Approach

**For Speculate**: Extend the CLI to generate a Claude Code plugin during `install`:

```
.claude/plugins/speculate/
├── .claude-plugin/plugin.json
├── commands/                    # Symlinks to shortcuts
│   └── new-plan-spec.md → docs/general/agent-shortcuts/shortcut:new-plan-spec.md
└── skills/
    └── speculate-workflow/
        └── SKILL.md             # Routing skill for auto-triggering
```

**Rationale**:
- Single source of truth in `docs/`
- Symlinks maintain compatibility
- Plugin provides namespacing (`/speculate:command`)
- Skill enables automatic workflow detection

### Alternative Approaches

1. **Standalone Skills**: Skip plugins, just create skills in `.claude/skills/`
   - Simpler but no command namespacing

2. **Marketplace Distribution**: Publish to a Claude Code marketplace
   - Better for public distribution but requires separate hosting

3. **Personal Installation**: Install to `~/.claude/` for cross-project availability
   - Good for individual developers, not teams

---

## References

### Official Documentation

- [Claude Code Skills](https://code.claude.com/docs/en/skills)
- [Claude Code Slash Commands](https://code.claude.com/docs/en/slash-commands)
- [Claude Code Plugins](https://code.claude.com/docs/en/plugins)
- [Skill Authoring Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [OpenAI Codex AGENTS.md](https://developers.openai.com/codex/guides/agents-md/)
- [OpenAI Codex Skills](https://developers.openai.com/codex/skills/)
- [Windsurf Cascade](https://docs.windsurf.com/windsurf/cascade/)

### Blog Posts and Articles

- [Equipping Agents with Agent Skills - Anthropic Engineering](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Building Skills for Claude Code - Claude Blog](https://claude.com/blog/building-skills-for-claude-code)
- [Skills for Claude - Jesse Vincent](https://blog.fsck.com/2025/10/16/skills-for-claude/)
- [Superpowers: How I'm using coding agents - Jesse Vincent](https://blog.fsck.com/2025/10/09/superpowers/)
- [Claude Skills Deep Dive - Lee Hanchung](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)
- [Claude Code Customization Guide - alexop.dev](https://alexop.dev/posts/claude-code-customization-guide-claudemd-skills-subagents/)

### Repositories

- [Anthropic Skills Repository](https://github.com/anthropics/skills)
- [Superpowers](https://github.com/obra/superpowers)
- [Claude Code](https://github.com/anthropics/claude-code)
- [AGENTS.md Specification](https://github.com/agentsmd/agents.md)

### Community Resources

- [Claude Plugins Community Registry](https://claude-plugins.dev/)
- [ClaudeLog - Tutorials & Best Practices](https://claudelog.com/)
- [Understanding Skills vs Commands vs Subagents vs Plugins](https://www.youngleaders.tech/p/claude-skills-commands-subagents-plugins)

---

## Appendices

### Appendix A: SKILL.md Template

```markdown
---
name: skill-name-gerund-form
description: Specific description with trigger keywords. State what it does AND when
  to use it. Max 1024 characters. Written in third person.
allowed-tools: [Read, Write, Bash, Grep]
model: claude-sonnet-4  # Optional
---

# Skill Title

## Overview

Brief description of what this skill does.

## When to Use

- Trigger scenario 1
- Trigger scenario 2

## Instructions

Step-by-step instructions for Claude to follow.

## Examples

### Example 1: [Scenario]

[Concrete example with expected behavior]

## Reference

See [reference.md](./reference.md) for detailed API documentation.
```

### Appendix B: Plugin Structure Template

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   ├── command-one.md
│   └── command-two.md
├── skills/
│   └── my-skill/
│       ├── SKILL.md
│       └── reference.md
├── hooks/
│   └── pre-commit.json
└── README.md
```

**plugin.json**:
```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "Plugin description for discovery",
  "author": {
    "name": "Author Name",
    "email": "author@example.com"
  }
}
```

### Appendix C: Cross-Platform Compatibility Matrix

| Feature | Claude Code | Codex | Cursor | Windsurf |
|---------|-------------|-------|--------|----------|
| AGENTS.md | ✅ (via CLAUDE.md) | ✅ Native | ✅ Reads | ❌ |
| SKILL.md | ✅ Native | ✅ Native | ❌ | ❌ |
| Slash Commands | ✅ Full | ✅ Limited | ❌ | ✅ Rulebooks |
| File Pattern Rules | ❌ | ❌ | ✅ globs | ❌ |
| Always Apply | Via skill description | Via directory | ✅ alwaysApply | ✅ Rules |
| Symlink Support | ✅ | ✅ | ✅ | ✅ |
| Plugin System | ✅ Full | ❌ | ❌ | ❌ |
