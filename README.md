# Agent Skills

[中文文档](README_CN.md)

A collection of AI agent skills — self-contained knowledge bases that can be loaded by AI coding assistants (e.g., Claude Code, Copilot CLI, Cursor) to gain expertise on specific topics.

## What is a Skill?

A skill is a directory with a `SKILL.md` entry point and optional supporting resources. It gives agents reusable task guidance and domain knowledge, with detail loaded as needed.

Each skill lives in its own directory under `skills/<name>/` and includes:

- **`SKILL.md`** — Entry point with frontmatter metadata and a quick-reference guide
- **Supporting Markdown** (optional) — Detailed syntax, edge cases, workflows, or templates in `references/`, `reference/`, or files alongside `SKILL.md`
- **`scripts/`** (optional) — Helper scripts for validation, inventory, or installation
- **`assets/`** (optional) — Templates and other resources used in generated output
- **`agents/`** (optional) — Agent-specific configuration and interface metadata

## Available Skills

| Skill                            | Description                                                                                                                                                                                             |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [database-design][database-design] | Relational database design and review — models, fields, keys, constraints, indexes, transaction rules, architecture, and compatible DDL/migrations for MySQL, PostgreSQL, and other relational databases |
| [drizzle-migration-conflict][drizzle-migration-conflict] | Drizzle Kit migration conflict diagnosis and team workflow guidance - inspect `_journal.json`, snapshots, migration folders, merge conflicts, `drizzle-kit check`, and CI prevention |
| [git-stack][git-stack] | Git workflows — commit and push changes, handle merge or rebase conflicts, and create or reuse worktrees, with scoped changes and reusable validation results |
| [grill][grill] | Decision interviews — examine a plan, idea, or design through successive questions, track dependent decisions in a design tree, and clarify assumptions until consensus |
| [hugo-to-markdown][hugo-to-markdown] | Hugo documentation and content conversion reference — inspect local Hugo config, shortcodes, render hooks, front matter, and mounted content roots to produce safe standard Markdown exports          |
| [postgresql-cli][postgresql-cli] | [PostgreSQL](https://www.postgresql.org/docs/current/app-psql.html) interactive terminal (psql) reference — meta-commands, CLI options, formatting, data import/export, scripting, and advanced workflows |
| [prd][prd] | Product requirements — turn ideas and clarified needs into a PRD covering users, goals, scope, behavior, and acceptance criteria before implementation |
| [pre-release-review][pre-release-review] | Production pre-release code review and deploy-readiness audit — inspect PRs or git ranges for missing migrations, configs, caches, queues, assets, secrets, service order, and rollout risks |
| [rclone-cli][rclone-cli]         | [Rclone](https://rclone.org/) cloud storage manager reference — terminal-based upload, download, sync, copy, move, mount, backup, filtering, encryption, bisync, and multi-provider remote management      |
| [redis-cli][redis-cli]           | [Redis](https://redis.io/docs/latest/develop/tools/cli/) command-line interface reference — Redis querying, keyspace inspection, monitoring, latency analysis, ACL and cluster management, scripting, and module workflows |
| [to-spec][to-spec] | Technical specifications — use PRD content by default; also accept explicitly supplied or selected ADRs, interviews, and Q&A documents, with source traceability, implementation contracts, and verification criteria |
| [to-task][to-task] | Task decomposition — create verifiable task plans with dependencies and acceptance criteria; ask where to save them, defaulting to feature directories with one Markdown file per task, with support for GitHub/GitLab Issues and explicitly selected available task systems |

## Installation

### npx skills (Recommended)

The [skills CLI](https://github.com/vercel-labs/skills) is a universal installer that supports Claude Code, Cursor, Copilot, Codex, and 40+ other agents.

```bash
# Install all skills from this repo
npx skills add chaunsin/agent-skills

# Install a specific skill
npx skills add chaunsin/agent-skills --skill postgresql-cli

# List available skills before installing
npx skills add chaunsin/agent-skills --list

# Install globally (available across all projects)
npx skills add chaunsin/agent-skills -g

# Install to specific agents
npx skills add chaunsin/agent-skills -a claude-code -a cursor

# Check if any installed skills have updates
npx skills check

# Update all installed skills to the latest version
npx skills update

# List all installed skills (project + global)
npx skills list

# Remove a specific skill
npx skills remove postgresql-cli
```

### Manual

```bash
# Copy a skill into the Claude Code skills directory
cp -r skills/<skill-name> ~/.claude/skills/
```

## Usage

Once installed, skills activate automatically based on their trigger keywords (defined in the `description` frontmatter field). No manual configuration is needed — when you ask a question related to a skill's domain, the agent will load the relevant reference.

For example, with the postgresql-cli skill installed, asking "how to list all tables in psql" or "psql \d commands" will trigger the skill.

For planning, use `grill` to examine unresolved decisions, `prd` to define product requirements, `to-spec` to define technical contracts, and `to-task` to produce a verifiable task plan. Choose the skill for the work you need; this is not a mandatory sequence. `to-spec` defaults to PRD content and also accepts other explicitly supplied or selected sources. Use `git-stack` when you need to commit, push, resolve conflicts, or prepare a worktree.

## Contributing

Before creating or changing a skill, follow [Skill Authoring and Maintenance](docs/skill-authoring.md). The guide covers concise and complete content, readable structure, progressive disclosure, evidence for changes, portability, security assessment, and validation.

## License

[Apache License 2.0](LICENSE)

[database-design]: skills/database-design/SKILL.md
[drizzle-migration-conflict]: skills/drizzle-migration-conflict/SKILL.md
[git-stack]: skills/git-stack/SKILL.md
[grill]: skills/grill/SKILL.md
[hugo-to-markdown]: skills/hugo-to-markdown/SKILL.md
[postgresql-cli]: skills/postgresql-cli/SKILL.md
[prd]: skills/prd/SKILL.md
[pre-release-review]: skills/pre-release-review/SKILL.md
[rclone-cli]: skills/rclone-cli/SKILL.md
[redis-cli]: skills/redis-cli/SKILL.md
[to-spec]: skills/to-spec/SKILL.md
[to-task]: skills/to-task/SKILL.md
