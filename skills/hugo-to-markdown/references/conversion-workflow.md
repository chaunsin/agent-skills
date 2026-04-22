# Conversion Workflow

## Purpose

Use this workflow when converting a Hugo documentation site into standard Markdown that no longer depends on Hugo runtime features.

## Step 1: Locate the real rule sources

Read these in order:

1. `hugo.toml`, `hugo.yaml`, `hugo.yml`, `hugo.json`, or `config/*`
2. `archetypes/*`
3. `data/*`
4. `layouts/_shortcodes/*` or `layouts/shortcodes/*`
5. `layouts/_markup/*`
6. Markdown- or JSON-facing export templates and partials such as `layouts/_default/*.md`, `layouts/_default/*.json`, or `layouts/partials/markdown-*.html`
7. `content/*`

For the Hugo docs fixture in this repository, also read:

1. `testdata/hugo/docs/hugo.toml`
2. `testdata/hugo/docs/archetypes/*.md`
3. `testdata/hugo/docs/layouts/_shortcodes/*.html`
4. `testdata/hugo/docs/layouts/_markup/*.html`
5. `testdata/hugo/docs/content/en/**/*.md`

## Step 2: Build a site inventory

Run:

```bash
python3 skills/hugo-to-markdown/scripts/inventory_hugo_rules.py \
  --site-root testdata/hugo/docs
```

Inspect the output for:

- content root and module mounts
- active shortcode names
- render hook names
- frequently used shortcodes
- front matter keys
- whether shortcode usage clusters around content graph expansion, section listings, data-backed tables, or external example extraction

Use the inventory to batch files by complexity:

- plain Markdown only
- front matter only
- literal Hugo documentation examples
- built-in shortcode usage
- content-graph shortcodes such as `include`, `embed-md`, `glossary-term`, and `table-children`
- custom shortcode usage
- data-backed shortcode usage
- render-hook-sensitive links and assets

## Step 3: Convert one slice at a time

Preferred order:

1. plain pages
2. pages with only front matter normalization
3. pages that mostly document Hugo syntax and contain literal shortcode examples
4. pages using shared includes
5. pages using custom shortcodes
6. pages whose content is partially generated from sections or data files
7. pages whose content depends on generated code examples or external local sources

This keeps regressions local and makes validation easier.

## Step 4: Materialize dynamic content

If a shortcode generates prose, lists, tables, or badges, replace it with the resulting Markdown.

Examples from the Hugo docs site:

- `include` pulls another content file and renders its shortcodes
- `quick-reference` expands section content
- `render-list-of-pages-in-section` builds a list from a section
- `render-table-of-pages-in-section` builds a table from section pages
- `glossary` materializes glossary content

Do not keep these as live Hugo shortcodes in the final standard Markdown.

When evaluating a shortcode, classify it first:

1. Static wrapper around inner Markdown or a simple asset
2. Content graph expansion into other pages or sections
3. Data-backed expansion using `data/*`
4. Generated example extraction from files outside the current page

This classification determines whether you can materialize the output directly, need recursive page resolution, need data-file reads, or must degrade to an explicit note.

## Step 5: Keep literal Hugo examples literal

The docs site frequently documents Hugo syntax itself. Distinguish:

- live shortcode calls that affect rendering
- escaped shortcode examples intended for readers

Common literal-example pattern:

```text
{{</* shortcode arg=value */>}}
```

When the construct is inside a fenced code block or otherwise clearly documentation, preserve it literally.

Also preserve escaped forms such as these when they appear in prose or tables:

```text
{{%/* foo */%}}
{{</* foo */>}}
```

Do not strip them just because they match a loose shortcode regex.

## Step 6: Normalize front matter before building derived content

Before using front matter to populate generated tables or lists:

- map reserved keys case-insensitively, for example `Title` to `title`
- treat `linkTitle` and `LinkTitle` as the same logical field
- preserve unknown custom keys as-is

This prevents empty links and missing descriptions when a repo mixes Hugo key casing conventions.

## Step 7: Validate aggressively

After each batch:

```bash
python3 skills/hugo-to-markdown/scripts/check_standard_markdown.py \
  --root /path/to/output
```

Treat validator hits as unresolved work unless they are deliberate examples inside code fences.

If you intentionally downgraded a shortcode to an explanatory note, that note should remain in the output and the original shortcode should not.
