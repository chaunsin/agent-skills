# CLAUDE.md

This file provides guidance to AI coding assistants when working with code in this repository.

## Repository Purpose

A collection of AI agent skills — self-contained Markdown knowledge bases that AI coding assistants (Claude Code, Copilot CLI, Cursor, etc.) load to gain expertise on specific topics. Skills are distributed via `npx skills add chaunsin/agent-skills`.

## Skill Anatomy

Each skill lives under `skills/<name>/`:

- `SKILL.md` — Entry point with YAML frontmatter (`name`, `description`, `metadata`) and a comprehensive quick reference
- `references/` — Modular deep-dive files linked from SKILL.md for detailed syntax, edge cases, and workflows
- `scripts/` — (optional) Helper scripts for validation, inventory, or installation
- `agents/` — (optional) Agent-specific configurations (e.g., OpenAI agent YAML)

The `description` frontmatter field is the **activation trigger** — it lists keywords and scenarios that cause the agent to load the skill.

`testdata/` holds source material used during skill authoring. It is gitignored and must not contain hardcoded absolute paths.

## Skill Authoring Conventions

- All skill content is written in **English** regardless of user language
- SKILL.md frontmatter fields: `name`, `description`, `metadata` (author, version)
- Cross-references between SKILL.md and reference files use **relative paths**
- Main SKILL.md provides a self-contained quick reference; `references/*.md` files split out detailed content
- README.md and README_CN.md must stay in sync when skills are added/removed

## Current Skills

| Skill              | Topic                                                                                                                                                            |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `hugo-to-markdown` | Hugo documentation and content conversion — inspect local Hugo config, shortcodes, render hooks, front matter, and mounted content roots to produce safe standard Markdown exports |
| `postgresql-cli` | PostgreSQL interactive terminal ([psql](https://www.postgresql.org/docs/current/app-psql.html)) — meta-commands, CLI options, formatting, import/export, scripting |
| `rclone-cli`     | [Rclone](https://rclone.org/) cloud storage manager — sync, copy, mount, serve, bisync, crypt, filtering, 70+ providers                                            |
| `redis-cli`      | [Redis](https://redis.io/docs/latest/develop/tools/cli/) command-line interface — data querying, key scanning, server monitoring, latency analysis, vector search, ACL management, cluster management, scripting |

## Development Commands

This repository contains Markdown documentation and helper scripts only. There is no build system, test suite, or package manager.

### Validate Hugo-to-Markdown output

```bash
# Detect leftover Hugo syntax and unsafe residue in generated Markdown
python3 skills/hugo-to-markdown/scripts/check_standard_markdown.py --root <markdown-output-dir>

# Inventory Hugo config, shortcodes, render hooks, and content patterns
python3 skills/hugo-to-markdown/scripts/inventory_hugo_rules.py --site-root <hugo-site-dir> --output inventory.json
```

### Install a skill locally

```bash
# Copy a skill into the Claude Code skills directory
cp -r skills/<skill-name> ~/.claude/skills/
```

## Git Conventions

- Conventional commit prefixes: `docs:`, `refactor:`, `feat:`, `init`
- Chinese commit messages are also accepted — follow the style of recent commits in the branch
