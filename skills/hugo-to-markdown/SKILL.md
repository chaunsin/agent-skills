---
name: hugo-to-markdown
description: >
  Convert Hugo documentation sites and Hugo-managed content into standard Markdown. Use when Codex needs
  to inspect a local Hugo repository, read hugo.toml or config files, content/, archetypes/, layouts/_shortcodes/,
  layouts/_markup/, and related docs content, then produce Markdown output with Hugo front matter, shortcodes,
  render hooks, ref/relref links, includes, and asset paths resolved or downgraded safely. This skill is especially
  useful for Hugo docs migrations, Hugo-to-Markdown exports, and repository-specific conversions where the local
  Hugo configuration and custom templates define the true rules.
metadata:
  author: chaunsin
  version: "0.2"
---

# Hugo To Markdown

## Overview

Use this skill when Markdown output must be derived from the local Hugo site, not guessed from generic Hugo knowledge. The conversion rules are the combination of Hugo's official behavior and the repository's own configuration, shortcode templates, render hooks, archetypes, and content conventions.

The target output is standard Markdown:

- Keep plain Markdown and YAML front matter.
- Replace or materialize Hugo-only constructs.
- Preserve meaning when exact rendering is not safely reproducible.
- Prefer explicit Markdown text over live Hugo template syntax.

## Official Basis

Treat the local Hugo docs snapshot as the primary ruleset for the repository under conversion. For the Hugo docs site in `testdata/hugo/docs/`, the most important rule sources are:

- `content/en/content-management/shortcodes.md`
- `content/en/templates/shortcode.md`
- `content/en/content-management/front-matter.md`
- `content/en/render-hooks/*.md`
- `hugo.toml`
- `layouts/_shortcodes/*.html`
- `layouts/_markup/*.html`
- `archetypes/*.md`

Do not assume built-in Hugo defaults if the repository overrides them locally.

## Workflow

### 1. Inventory the site before converting files

Always inspect the site-level rules first.

```bash
python3 scripts/inventory_hugo_rules.py --site-root /path/to/hugo-site
```

For the local test fixture in this repository:

```bash
python3 skills/hugo-to-markdown/scripts/inventory_hugo_rules.py \
  --site-root testdata/hugo/docs
```

This inventory step is mandatory for batch work. It identifies:

- active config files
- module mounts and content roots
- custom shortcodes
- custom render hooks
- front matter keys seen in content
- shortcode usage across content files

### 2. Convert with repository rules, not generic heuristics

Read `references/conversion-workflow.md` before changing files. Then:

1. Resolve the real content root from `hugo.toml`, `config.*`, and module mounts.
2. Read archetypes to understand expected front matter shape.
3. Read site data sources in `data/` when shortcodes or partials pull structured content from them.
4. Read custom shortcode templates in `layouts/_shortcodes/` or `layouts/shortcodes/`.
5. Read render hooks in `layouts/_markup/`.
6. Check whether the repo already defines Markdown- or JSON-facing export templates and partials; if it does, use those as evidence for how the site itself downgrades Hugo constructs.
7. Follow `include`-style shortcodes into referenced content files when the docs site composes content from shared fragments.
8. Convert one file or one coherent section at a time.

### 3. Preserve semantics during conversion

Use these rules by default:

- Keep YAML front matter unless the user explicitly asks for front-matter-free Markdown.
- Preserve core fields such as `title`, `description`, `date`, `draft`, `aliases`, `slug`, `url`, `weight`, and nested `params` when they still carry meaning.
- Normalize reserved Hugo front matter keys to their canonical names when the repo mixes casing, for example `Title` to `title`, `Description` to `description`, and `LinkTitle` to `linkTitle`.
- Convert Hugo internal links to normal Markdown links with resolved destinations.
- Replace Hugo shortcodes with plain Markdown, HTML, or explicit notes only after reading the local shortcode implementation.
- Materialize dynamically generated lists and tables when the shortcode renders content from sections or data files.
- Leave literal Hugo examples unchanged when the document is documenting Hugo syntax rather than invoking it. This applies both inside fenced code blocks and to escaped forms such as `{{</* foo */>}}` or `{{%/* foo */%}}` that appear in prose, tables, or notation examples.

### 4. Apply Hugo-specific body rules carefully

The Hugo docs repository under `testdata/hugo/docs/` has several important local behaviors:

- `hugo.toml` mounts `content/en` to the logical `content` root, so link and include resolution must use Hugo logical paths instead of preserving `/en/` blindly.
- `include` renders another page through `RenderShortcodes`; follow the referenced content file and inline the resulting Markdown.
- `quick-reference`, `render-list-of-pages-in-section`, and `render-table-of-pages-in-section` generate navigation content from sections; replace them with materialized Markdown lists or tables.
- `glossary-term`, `glossary`, `get-page-desc`, `module-mounts-note`, `new-in`, and `deprecated-in` expand to prose or badges; convert them into explicit Markdown text or callouts.
- `code-toggle` may read config snippets and data-backed examples; preserve the underlying code sample, not the UI toggle.
- if the repo has data-backed or example-extraction shortcodes such as `features-table`, `optional-features-table`, `clients-example`, or `jupyter-example`, inspect the referenced `data/` files, local example sources, and Markdown-export partials before deciding whether to materialize or downgrade.
- glossary links can use the special Markdown destination `(g)`; resolve these to stable glossary links instead of leaving the placeholder.
- `img` and `imgproc` are presentation helpers around page, global, or remote resources; preserve the underlying image reference and caption semantics.
- `eturl` emits links to embedded template sources; convert to a normal Markdown link if the destination is known, otherwise preserve as a textual note.
- blockquote and code-block render hooks add alert, file-label, summary, and detail semantics; preserve these semantics in Markdown or explicit notes.

Read `references/shortcodes-and-render-hooks.md` before converting any file that contains Hugo syntax.

### 5. Validate the output

After conversion, scan the generated Markdown for leftover Hugo-only syntax.

```bash
python3 skills/hugo-to-markdown/scripts/check_standard_markdown.py \
  --root /path/to/output
```

If the validator reports active Hugo syntax outside code fences, either:

- resolve it fully, or
- replace it with a safe textual explanation

Do not silently ship unresolved `{{< ... >}}`, `{{% ... %}}`, or Go template expressions.

### 6. Downgrade explicitly when full materialization is not safe

If a shortcode depends on build-time data, generated examples, or external source files that you cannot resolve deterministically from the local repo snapshot, replace it with an explicit Markdown note.

Use a short, boring format such as:

- `> Conversion note: <what the shortcode normally renders>.`
- followed by any safe subset you were able to preserve, such as inline Redis CLI text, a resolved image URL, or a known section list

Do not leave empty links, broken table cells, or stripped content with no explanation.

## Repo-Specific Notes For `testdata/hugo/docs`

Use these facts when the local Hugo docs fixture is the input:

- `hugo.toml` mounts `content/en` to `content`, so English docs are the active content tree.
- Goldmark passthrough delimiters are configured for math, so `$$...$$`, `\\(...\\)`, and `\\[...\\]` can be meaningful content, not junk.
- `markup.goldmark.parser.attribute.block = true`, so block attribute syntax may appear after fenced blocks and other block elements.
- The repo uses custom render hooks for blockquotes, code blocks, links, passthrough, and tables.
- The repo uses many shared `_common` fragments referenced through `% include %`, so reading a page file alone is not enough to understand the rendered content.
- The repo contains many escaped shortcode examples such as `{{</* foo */>}}` and `{{%/* foo */%}}`; these are documentation samples and must remain literal when they appear inside code examples, notation tables, or tutorial prose.

## Safety Rules

- Never execute Hugo templates, shortcodes, or Go template expressions.
- Never treat content files as trusted executable input.
- Never run `hugo`, `npm install`, `go install`, downloaded shell installers, or any network install step unless the user explicitly asks for it.
- Keep all conversion scripts offline and deterministic.
- Restrict reads to the declared site root and writes to the declared output root.
- Reject path traversal, symlink escape, or attempts to write outside the requested output directory.
- Do not leak local absolute paths, secrets, environment variables, or git credentials into generated Markdown.
- When exact rendering cannot be reproduced safely, degrade to explicit Markdown text instead of live Hugo syntax.

## Resources

Read these files as needed:

- `references/conversion-workflow.md`
  End-to-end process for repo-aware conversion.
- `references/front-matter-and-content.md`
  Front matter mapping, common content conventions, and literal-example handling.
- `references/shortcodes-and-render-hooks.md`
  Hugo shortcode notation, docs-site custom shortcodes, and render-hook implications.
- `references/links-assets-and-validation.md`
  Link resolution, assets, validation, and residue triage.

Use these scripts when helpful:

- `scripts/inventory_hugo_rules.py`
  Scan a Hugo site and emit a rule inventory.
- `scripts/check_standard_markdown.py`
  Detect leftover Hugo syntax and common unsafe residue in Markdown output.
