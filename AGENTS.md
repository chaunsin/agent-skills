# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

A collection of AI agent skills — self-contained Markdown knowledge bases that AI coding assistants (Claude Code, Copilot CLI, Cursor, etc.) load to gain expertise on specific topics. Skills are distributed via `npx skills add chaunsin/agent`.

## Skill Anatomy

Each skill lives under `skills/<name>/`:

- `SKILL.md` — Entry point with YAML frontmatter (`name`, `description`, `metadata`) and a comprehensive quick reference
- `references/` — Modular deep-dive files linked from SKILL.md for detailed syntax, edge cases, and workflows
- `scripts/` — (optional) Helper scripts, e.g. installers

The `description` frontmatter field is the **activation trigger** — it lists keywords and scenarios that cause the agent to load the skill.

`testdata/` holds source material used during skill authoring (gitignored).

## Skill Authoring Conventions

- All skill content is written in **English** regardless of user language
- SKILL.md frontmatter fields: `name`, `description`, `metadata` (author, version)
- Cross-references between SKILL.md and reference files use **relative paths**
- Main SKILL.md provides a self-contained quick reference; `references/*.md` files split out detailed content
- README.md and README_CN.md must stay in sync when skills are added/removed

## Current Skills

| Skill | Topic |
|-------|-------|
| `postgresql-cli` | PostgreSQL interactive terminal (psql) — meta-commands, CLI options, formatting, import/export, scripting |
| `rclone-cli` | Rclone cloud storage manager — sync, copy, mount, serve, bisync, crypt, filtering, 70+ providers |

## Git Conventions

- Conventional commit prefixes: `docs:`, `refactor:`, `feat:`, `init`
- Chinese commit messages are also accepted — follow the style of recent commits in the branch
