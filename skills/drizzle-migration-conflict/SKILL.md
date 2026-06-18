---
name: drizzle-migration-conflict
description: >
  Diagnose, repair, and prevent Drizzle Kit migration conflicts in team workflows.
  Use this skill whenever the user mentions drizzle-kit migration conflicts, Drizzle ORM
  migrations, _journal.json, snapshot.json, non-commutative migrations, migration folder
  conflicts, merge or rebase conflicts in generated Drizzle migrations, drizzle-kit check,
  drizzle-kit generate, or asks how multiple developers should coordinate database migrations.
  Prefer this skill even when the user only says a Drizzle migration file conflicts after a
  pull, merge, rebase, or PR update.
metadata:
  author: chaunsin
  version: "0.1"
---

# Drizzle Migration Conflict

Use this skill to help a user diagnose, repair, and prevent Drizzle Kit migration conflicts in a
multi-developer repository. Drizzle migrations encode both SQL and migration snapshots, so the safe
answer depends on the current migration directory shape, the Drizzle Kit version, and the git state.

## Safety rules

- Start in read-only diagnosis mode unless the user explicitly asks to fix files.
- Do not run `drizzle-kit migrate`, `drizzle-kit push`, database seed scripts, or any command that
  connects to a live database unless the user explicitly requests it and the target is clear.
- Treat `drizzle-kit check`, project typechecks, and tests as command execution that may load project
  config, environment variables, or scripts. Inspect scripts/config first, and require an explicit
  non-production or disposable target before any DB-backed validation.
- Do not delete migration files, rewrite `_journal.json`, or run `git checkout --ours`,
  `git checkout --theirs`, `git restore`, or `rm` unless the user has confirmed the exact side and
  files to change.
- Do not recommend `drizzle-kit push` as the production solution for migration conflicts; it skips
  the auditable migration history that teams need.
- Treat `--ignore-conflicts` as an exception for a known false positive, not as the normal fix.
- Preserve schema source code changes unless the user explicitly asks to discard them. Conflict
  repair normally discards generated migrations and regenerates them from the merged schema.
- If `ours` and `theirs` could mean different branches depending on merge direction, ask the user to
  identify the parent branch before suggesting checkout commands.

## Required references

- Read `references/sources.md` when the answer depends on current Drizzle behavior, official
  guidance, or one of the preserved external links.
- Read `references/conflict-resolution.md` before recommending a repair flow.
- Read `references/ci-policy.md` before proposing CI, merge queue, or team workflow changes.
- Read `references/report-template.md` before writing a diagnostic report.

## Source references

Keep these links available for recursive verification and future updates:

- Drizzle discussion 1104: https://github.com/drizzle-team/drizzle-orm/discussions/1104
- Drizzle discussion 2832: https://github.com/drizzle-team/drizzle-orm/discussions/2832
- Drizzle discussion 5005: https://github.com/drizzle-team/drizzle-orm/discussions/5005
- Drizzle discussion 5581: https://github.com/drizzle-team/drizzle-orm/discussions/5581
- Drizzle Kit generate docs: https://orm.drizzle.team/docs/drizzle-kit-generate
- Drizzle Kit check docs: https://orm.drizzle.team/docs/drizzle-kit-check
- Drizzle migrations docs: https://orm.drizzle.team/docs/migrations
- Legacy undo gist: https://gist.github.com/anthonyjoeseph/102c0e3ea8496fe111029a8b8a95cc3a
- Legacy repair gist: https://gist.github.com/anthonyjoeseph/6b99beb34d494acd1dfc83a192ed9388
- Earlier repair script variant: https://gist.github.com/gburtini/7e34842c567dd80ee834de74e7b79edd
- GitHub merge queue docs: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue

## Mode selection

Classify the task first:

1. **Diagnose** - The user has a conflict or failed `drizzle-kit check` and wants to understand it.
2. **Repair** - The user explicitly asks to fix or regenerate migration files.
3. **CI hardening** - The user wants to prevent future conflicts in PRs or merge queues.
4. **Explain** - The user wants a conceptual answer or a team playbook.

When the mode is not explicit, choose Diagnose.

## Repository discovery

Collect repo facts before giving commands:

```bash
git status --short
git rev-parse --show-toplevel
git rev-parse --abbrev-ref HEAD
git ls-files -u
rg --files -g 'drizzle.config.*' -g 'package.json' -g 'pnpm-lock.yaml' -g 'yarn.lock' -g 'package-lock.json'
```

Then inspect the relevant files:

- `drizzle.config.*` for `out`, `schema`, dialect, and config shape.
- `package.json` scripts for the project-approved `generate`, `check`, and `migrate` commands.
- `package.json` dependencies or lockfile snippets for `drizzle-kit` and `drizzle-orm` versions.
- The migration output directory, either from config or common names like `drizzle/`, `migrations/`,
  or `src/db/migrations/`.

If this skill's helper script is available, run it in read-only mode:

```bash
python3 <skill-dir>/scripts/check_drizzle_migrations.py --root .
```

Resolve `<skill-dir>` to the installed skill directory. If the target repository vendors this skill,
that path may be `skills/drizzle-migration-conflict`. Use `--config <file>` and
`--migrations-dir <dir>` when the project has multiple Drizzle configs or outputs.

## Migration structure decision

Identify the structure before proposing a fix:

- **Legacy structure**: `<out>/meta/_journal.json`, `<out>/meta/*_snapshot.json`, and root-level
  migration SQL files such as `<out>/0003_name.sql`.
- **Folder-based structure**: each migration is a directory containing `migration.sql` and
  `snapshot.json`.
- **Unknown or mixed structure**: stop and report ambiguity. Do not guess a destructive repair.

## Recommended repair principles

- Resolve schema source conflicts first. The regenerated migration must reflect the merged schema,
  not one side's stale snapshot.
- Treat the parent or target branch migration history as the source of truth when repairing a feature
  branch after updating from that branch.
- Prefer discarding and regenerating generated migration artifacts over hand-editing journal or
  snapshot files.
- After regeneration, validate in tiers: database-free structural checks first; then `drizzle-kit
  check` only after confirming its config/env cannot point at production; then project tests only
  after inspecting the scripts and any database targets.
- If the user asks to apply changes, state exactly which files will be changed before performing the
  write.

## Output rules

- Use the user's language when practical, but keep command snippets and file paths literal.
- State the detected migration structure and selected mode.
- Separate confirmed conflicts from assumptions and missing evidence.
- Give a safe default path first, then optional automation or CI hardening.
- For destructive steps, label them as "requires confirmation" and explain what will be lost.
- Use the conclusion values from `references/report-template.md` for diagnostic reports.

## Test prompts

Use these prompts to validate the skill behavior:

- "My Drizzle `_journal.json` and `0003_snapshot.json` conflict during merge. Tell me what to do."
- "We upgraded to the migration folder layout and `drizzle-kit check` reports a non-commutative conflict."
- "Design CI so our team stops merging broken Drizzle migrations."
- "Can I solve this production Drizzle migration conflict with `drizzle-kit push`?"
- "Use the links in the skill to re-check the current official Drizzle migration conflict guidance."
