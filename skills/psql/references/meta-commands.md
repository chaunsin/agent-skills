# psql Meta-Commands — Complete Reference

Comprehensive reference for all psql backslash commands, organized by category. This covers every meta-command from the official PostgreSQL documentation.

## Table of Contents

- [General](#general)
- [Connection Management](#connection-management)
- [Query Execution](#query-execution)
- [Object Inspection (\d family)](#object-inspection-d-family)
- [Data Import/Export](#data-importexport)
- [Large Objects](#large-objects)
- [Output Formatting](#output-formatting)
- [Scripting and Control Flow](#scripting-and-control-flow)
- [Pipeline Mode](#pipeline-mode)
- [Session Management](#session-management)
- [Help and Information](#help-and-information)

---

## The Query Buffer

psql maintains an internal **query buffer** — a working area where SQL commands are assembled before being sent to the server. Understanding how the buffer works clarifies the behavior of many meta-commands:

- **Typing SQL** (without a terminating semicolon) appends text to the query buffer.
- **Semicolon (`;`)** sends the buffer contents to the server and clears it.
- **`\r` / `\reset`** discards the buffer without executing it.
- **`\p` / `\print`** displays the current buffer contents.
- **`\w` / `\write`** writes the buffer to a file or pipe.
- **`\e` / `\edit`** opens the buffer in an external editor; when the editor closes, the modified content is re-parsed — complete queries (those ending with `;`) are executed immediately, and any remaining text stays in the buffer.
- **`\g`** sends the buffer like a semicolon but accepts optional formatting and output-redirection arguments.
- Many meta-commands that operate on "the query buffer" fall back to the most recently executed query if the buffer is empty (e.g., `\g`, `\gdesc`, `\p`).

---

## Meta-Command Argument Parsing

Most meta-commands accept arguments. Understanding how psql parses these arguments is essential for using them correctly, especially in scripts.

### Quoting Rules

Arguments are separated by whitespace. To include whitespace in an argument:

- **Single quotes**: `'hello world'` — the argument is `hello world`. Single quotes prevent variable interpolation and backquote expansion.
- **Double quotes**: `"hello world"` — the argument is `hello world`. Variable interpolation (`:varname`) IS performed inside double quotes, but backquote expansion is NOT.
- **Unquoted**: Arguments are delimited by whitespace; no quoting needed for single tokens.

### C-like Escape Sequences

Within single-quoted strings, these C-like escape sequences are recognized:

| Escape | Meaning |
|--------|---------|
| `\n` | Newline |
| `\t` | Tab |
| `\b` | Backspace |
| `\r` | Carriage return |
| `\f` | Form feed |
| `\digits` | Octal byte value |
| `\xhexdigits` | Hexadecimal byte value |

A backslash followed by any other character is treated as that character literally (e.g., `\\` → `\`, `\'` → `'`).

### Variable Interpolation in Arguments

psql variable references (`:varname`) are expanded in meta-command arguments wherever they appear, EXCEPT inside single-quoted strings. Double-quoted strings DO expand variable references.

```sql
\set dest '/tmp/output.txt'
\echo :dest              -- expands to /tmp/output.txt
\echo ':dest'            -- literal :dest (no expansion)
\echo ":dest"            -- expands to /tmp/output.txt
```

### Testing Variable Existence with `:{?varname}`

The syntax `:{?variable_name}` tests whether a variable is defined. It expands to `TRUE` or `FALSE` (literally), making it useful in `\if` conditions:

```sql
\if :{?myvar}
  \echo 'myvar is defined'
\else
  \echo 'myvar is not defined'
\endif
```

### Backquote Expansion

Text enclosed in backquotes (`` ` ``) within meta-command arguments is executed as a shell command, and its standard output (with trailing newlines removed) replaces the backquoted text. This is useful for injecting dynamic values:

```sql
\echo `date`                    -- shows current date
\echo `whoami`                  -- shows current OS user
\set mydate `date +%Y%m%d`
\echo :mydate                   -- e.g., 20260402
```

Backquote expansion is NOT performed inside single-quoted strings or in lines that are skipped by `\if`/`\else`/`\elif`.

**Variable interpolation inside backquotes**: psql variable references (`:varname`, `:'varname'`) are expanded within backquoted text before the shell command is executed. This means you can use psql variables in shell commands:

```sql
\set logfile /tmp/query.log
\echo `cat :logfile`              -- expands :logfile before running cat
\echo `echo :'%varname'`          -- :'...' form is preferred for shell safety
```

The `:'varname'` form (quoted) is preferred inside backquotes because it properly escapes special characters. However, `:'varname'` will error if the variable value contains carriage return (`\r`) or line feed (`\n`) characters.

### SQL Identifier Arguments

Some meta-commands take arguments that describe database objects (e.g., `\df`, `\ef`). These follow special rules:

- Unquoted names are folded to lowercase (matching SQL identifier behavior)
- Double-quoted names preserve case: `\df "MyFunction"`
- Mixed quoting: unquoted parts are folded, double-quoted parts are preserved. `FOO"BAR"BAZ` becomes `fooBARbaz`
- Trailing `()` with optional type names specifies argument types: `\df my_func(integer, text)`
- `*` matches all: `\df *`

### Argument Parsing Stop Rules

- The entire remainder of the line is taken as the argument for commands like `\!`, `\copy`, `\o |command`, `\echo` (after processing quoting and interpolation).
- A `\\` (double backslash) anywhere in the argument text causes psql to stop parsing at that point — everything before `\\` is the argument, everything after is ignored. This is useful for adding inline comments:
  ```sql
  \echo hello \\ this is a comment
  -- outputs: hello
  ```

---

## General

### `\;`

Appends a semicolon to the query buffer without triggering command execution. This allows combining multiple SQL statements into a single server request:

```sql
select 1\; select 2\; select 3;
```

All three statements are sent in one request when the non-backslashed semicolon is reached. The server executes them as a single transaction unless explicit `BEGIN`/`COMMIT` is included.

### `\! [command]`

With no argument, escapes to a sub-shell (psql resumes when sub-shell exits). With an argument, executes the shell command. The entire remainder of the line is taken as the command — no variable interpolation or backquote expansion.

```sql
\! ls -la /tmp
\! pwd
```

### `\copyright`

Shows the copyright and distribution terms of PostgreSQL.

---

## Connection Management

### `\c` or `\connect [ -reuse-previous=on|off ] [ dbname [ username ] [ host ] [ port ] | conninfo ]`

Establishes a new connection to a PostgreSQL server. If the connection succeeds, the previous connection is closed.

**Positional syntax:**
```sql
\c mydb myuser host.dom 6432
\c - - newhost -              -- change only the host
```

**Connection string syntax:**
```sql
\c service=foo
\c "host=localhost port=5432 dbname=mydb connect_timeout=10 sslmode=disable"
\c postgresql://tom@localhost/mydb?application_name=myapp
```

**`-reuse-previous` flag:**
- By default, parameters are re-used in positional syntax, but NOT with conninfo strings
- Pass `-reuse-previous=on` to re-use all unspecified parameters from the current connection
- Pass `-reuse-previous=off` to prevent re-use

```sql
\c -reuse-previous=on sslmode=require    -- changes only sslmode
```

**Behavior on failure:**
- Interactive mode: previous connection is kept
- Script mode: previous connection is closed; all database commands fail until next successful `\c`

### `\conninfo`

Outputs connection information including database, user, host, port, and SSL status. The `Client User` field shows the user at connection time; `Superuser` shows whether the current execution context has superuser privileges (may differ after `SET ROLE`).

### `\encoding [ encoding ]`

Sets the client character set encoding. Without an argument, shows the current encoding.

### `\password [ username ]`

Changes the password for the specified user (default: current user). Prompts for the new password, encrypts it, and sends it as `ALTER ROLE`. The new password does NOT appear in command history, server log, or anywhere else.

---

## Query Execution

### `\g [ (option=value [...]) ] [ filename ]` / `\g [ (option=value [...]) ] [ |command ]`

Sends the current query buffer to the server for execution.

- Without arguments: equivalent to a semicolon
- With a filename: output written to file
- With `|command`: output piped to shell command (no variable interpolation in command)
- With `(option=value)`: one-shot formatting options (same as `\pset` options)

```sql
SELECT * FROM users \g (format=csv,footer=off) /tmp/users.csv
SELECT count(*) FROM users \g | wc -l
```

If the query buffer is empty, the most recently sent query is re-executed.

### `\gx [ (option=value [...]) ] [ filename ]`

Like `\g`, but forces expanded output mode for this query (as if `expanded=on` were included).

### `\gdesc`

Shows the column names and data types of the result without actually executing the query. Syntax errors are still reported. If the query buffer is empty, describes the most recently sent query.

### `\gset [ prefix ]`

Executes the query and stores the result in psql variables. The query must return exactly one row. Each column becomes a variable named after the column (optionally prefixed). NULL columns unset the variable rather than setting it. If the query fails or does not return one row, no variables are changed.

```sql
SELECT 'hello' AS var1, 10 AS var2
\gset result_
\echo :result_var1 :result_var2
-- outputs: hello 10
```

### `\gexec`

Executes the current query, then treats each column of each row as a SQL statement to execute. NULL fields are ignored. Generated queries are sent literally — no psql meta-commands or variable references. Execution continues on error unless `ON_ERROR_STOP` is set. Setting `ECHO` to `all` or `queries` is recommended when using `\gexec` to see what's being executed.

```sql
SELECT format('CREATE INDEX ON my_table(%I)', attname)
FROM pg_attribute
WHERE attrelid = 'my_table'::regclass AND attnum > 0
ORDER BY attnum
\gexec
```

### `\crosstabview [ colV [ colH [ colD [ sortcolH ] ] ] ]`

Executes the query and displays results as a crosstab (pivot table). The query must return at least three columns. Column specs can be column numbers (1-based) or names.

- `colV` — vertical header (default: column 1)
- `colH` — horizontal header (default: column 2, must differ from colV)
- `colD` — data displayed in the grid (default: the remaining column)
- `sortcolH` — optional sort column for horizontal header (must be integers)

Error is reported if multiple rows map to the same cell.

### `\bind [ parameter ] ...`

Sets query parameters for the next query execution. Uses the extended query protocol. Can be combined with `\g`, `\gx`, or `\gset`:

```sql
INSERT INTO tbl1 VALUES ($1, $2) \bind 'first value' 'second value' \g
SELECT * FROM tbl1 WHERE id = $1 \bind 'first value' \gx
SELECT id, name FROM tbl1 WHERE id = $1 \bind 'first value' \gset result_
```

### `\bind_named statement_name [ parameter ] ...`

Like `\bind`, but takes the name of an existing prepared statement as the first parameter.

```sql
INSERT INTO tbls1 VALUES ($1, $2) \parse stmt1
\bind_named stmt1 'first value' 'second value' \g
```

### `\parse statement_name`

Creates a prepared statement from the current query buffer. An empty string denotes the unnamed prepared statement.

```sql
SELECT $1 \parse stmt1
```

### `\close_prepared statement_name`

Closes the specified prepared statement. No-op if it doesn't exist.

```sql
SELECT $1 \parse stmt1
\close_prepared stmt1
```

---

## Object Inspection (\d family)

All `\d` commands accept these common modifiers:
- `+` — extra info (size, description, ownership)
- `S` — include system objects
- `x` — expanded display (must follow `S` or `+`, NOT immediately after `\d`)

**Important**: The `x` modifier for expanded display must appear after `S` or `+` (e.g., `\dt+x`), because `\dx` is a separate command that lists installed extensions. Writing `\dx` when you meant expanded display will show extensions instead.

All accept a pattern parameter with wildcard matching (`*`, `?`, regex). See Patterns section below.

### `\d[Sx+] [ pattern ]`

Without a pattern: equivalent to `\dtvmsE` (lists all visible tables, views, materialized views, sequences, and foreign tables).

With a pattern: shows columns, types, tablespace, special attributes (NOT NULL, defaults), indexes, constraints, rules, triggers. For foreign tables, shows the foreign server.

`\d+` adds: column comments, OID presence, view definition, replica identity, access method.

### Table-type listing commands

`\dE` / `\di` / `\dm` / `\ds` / `\dt` / `\dv` — List foreign tables, indexes, materialized views, sequences, tables, or views. Combine letters: `\dti` lists both tables and indexes.

`\d+` adds: persistence status (permanent/temporary/unlogged), physical size on disk, description.

### Aggregate and function listings

| Command | Shows |
|---------|-------|
| `\da[Sx] [pattern]` | Aggregate functions with return type and input types |
| `\df[anptwSx+] [pattern [arg_pattern ...]]` | Functions. Filter by type: `a`=agg, `n`=normal, `p`=procedure, `t`=trigger, `w`=window. Additional args match parameter type names. Use `-` as last arg_pattern to prevent matching functions with extra args. Example: `\df * integer` lists functions whose first argument is `integer`. |
| `\do[Sx+] [pattern [arg_pattern [arg_pattern]]]` | Operators with operand/result types. One arg matches prefix operators; two args match binary operators. Use `-` for unused operand. Example: `\do + integer integer` lists `+` operators with two integer args. |

### Schema and type listings

| Command | Shows |
|---------|-------|
| `\dn[Sx+] [pattern]` | Schemas (namespaces) |
| `\dT[Sx+] [pattern]` | Data types (`\dT+` shows internal name, size, enum values, permissions) |
| `\dC[x+] [pattern]` | Type casts (`\dC+` shows leakproof status and description) |
| `\dD[Sx+] [pattern]` | Domains (`\dD+` shows permissions and description) |
| `\dO[Sx+] [pattern]` | Collations (only collations usable with current database encoding — results vary by database) |

### Access method and operator listings

| Command | Shows |
|---------|-------|
| `\dA[x+] [pattern]` | Access methods |
| `\dAc[x+] [am_pattern [type_pattern]]` | Operator classes |
| `\dAf[x+] [am_pattern [type_pattern]]` | Operator families |
| `\dAo[x+] [am_pattern [family_pattern]]` | Operators in families |
| `\dAp[x+] [am_pattern [family_pattern]]` | Support functions in families |

### Configuration and privilege listings

| Command | Shows |
|---------|-------|
| `\dconfig[x+] [pattern]` | Server config parameters. Without a pattern, shows only non-default values. `\dconfig+` adds data type, context, and access privileges. |
| `\dp[Sx] [pattern]` | Table/view/sequence privileges |
| `\ddp[x] [pattern]` | Default access privileges |
| `\drg[Sx] [pattern]` | Granted role memberships (ADMIN, INHERIT, SET options, grantor) |
| `\drds[x] [role_pattern [db_pattern]]` | Per-role and per-database config settings |
| `\z[Sx] [pattern]` | Alias for `\dp` |

### Replication and partition listings

| Command | Shows |
|---------|-------|
| `\dP[itnx+] [pattern]` | Partitioned relations (`t`=tables, `i`=indexes, `n`=nested shows parent) |
| `\dRp[x+] [pattern]` | Replication publications (`\dRp+` shows associated tables/schemas) |
| `\dRs[x+] [pattern]` | Replication subscriptions (`\dRs+` shows additional properties) |

### Extended statistics, extensions, and more

| Command | Shows |
|---------|-------|
| `\dX[x] [pattern]` | Extended statistics. Status column shows `defined` (requested) or NULL (not requested) per statistic kind. Use `pg_stats_ext` to check if `ANALYZE` has been run. |
| `\dx[x+] [pattern]` | Installed extensions (`\dx+` lists all objects in each extension) |
| `\dy[x+] [pattern]` | Event triggers |
| `\dd[Sx] [pattern]` | Object descriptions (comments on constraints, operator classes, operator families, rules, triggers). Other object comments are shown by their respective `\d` commands. |

### Foreign data wrapper listings

| Command | Shows |
|---------|-------|
| `\des[x+] [pattern]` | Foreign servers |
| `\det[x+] [pattern]` | Foreign tables (`\det+` shows options and description) |
| `\deu[x+] [pattern]` | User mappings (CAUTION: `\deu+` may show passwords) |
| `\dew[x+] [pattern]` | Foreign-data wrappers |

### Text search listings

| Command | Shows |
|---------|-------|
| `\dF[x+] [pattern]` | Text search configurations (`\dF+` shows parser and dictionary list per token type) |
| `\dFd[x+] [pattern]` | Text search dictionaries |
| `\dFp[x+] [pattern]` | Text search parsers (`\dFp+` shows functions and recognized token types) |
| `\dFt[x+] [pattern]` | Text search templates |

### Other object listings

| Command | Shows |
|---------|-------|
| `\db[x+] [pattern]` | Tablespaces (`\db+` shows options, size, permissions, description) |
| `\dc[Sx+] [pattern]` | Character-set encoding conversions |
| `\dl[x+]` | Large objects (alias for `\lo_list`) |
| `\dL[Sx+] [pattern]` | Procedural languages |
| `\du[Sx+] [pattern]` / `\dg[Sx+] [pattern]` | Database roles (`\du` = `\dg`, since users and groups were unified into roles) |
| `\l[x+] [pattern]` | Databases (`\l+` shows size, default tablespace, description. Size only available for databases you can connect to.) |
| `\sf[+] func_desc` | Function definition (read-only, `+` numbers lines from body start) |
| `\sv[+] view_name` | View definition (read-only, `+` numbers lines) |

### Pattern matching rules

All `\d` commands that accept a pattern use the same matching system:

1. **Case folding**: Unquoted letters are folded to lowercase (like SQL identifiers). Double quotes prevent folding.
2. **Wildcards**: `*` matches any character sequence, `?` matches any single character. Within double quotes, these are literal.
3. **Dot separator**: A dot (`.`) separates schema from object name. Two dots separate database.schema.object (database must match current connection).
4. **Regex**: Advanced patterns like `[0-9]` work. `.` is a separator (not regex any-char), `*` → `.*`, `?` → `.`, `$` is literal. Within double quotes, all regex specials are literal.
5. **No pattern**: Shows all objects visible in the current schema search path (equivalent to `*`). Use `*.*` to see all objects regardless of visibility.

---

## Data Import/Export

### `\copy`

Performs a client-side copy. Unlike SQL `COPY`, this runs with the client's filesystem and permissions (no superuser required).

```
\copy { table [(column_list)] } FROM { 'filename' | program 'command' | stdin | pstdin }
      [ [ WITH ] ( option [, ...] ) ] [ WHERE condition ]

\copy { table [(column_list)] | (query) } TO { 'filename' | program 'command' | stdout | pstdout }
      [ [ WITH ] ( option [, ...] ) ]
```

**Key behaviors:**
- The entire remainder of the line is always taken as arguments (no variable interpolation or backquote expansion)
- For `FROM stdin`, data continues until `\.` or EOF
- `pstdin`/`pstdout` always use psql's actual stdin/stdout regardless of `\o` setting
- All options other than source/destination are as specified for SQL `COPY`

**WARNING**: `program 'command'` executes a shell command with client user privileges. Never concatenate untrusted input.

**Tip**: For multi-line copy or variable interpolation, use `COPY ... TO STDOUT` terminated with `\g filename` or `\g |command`.

---

## Large Objects

### `\lo_export loid filename`

Reads the large object with the given OID from the database and writes it to the specified file. Uses client-side permissions (unlike server-side `lo_export`).

### `\lo_import filename [ comment ]`

Imports a file as a large object. Returns the OID assigned. Always provide a human-readable comment.

```sql
\lo_import '/home/user/photo.jpg' 'product photo'
-- Returns: lo_import 152801
```

### `\lo_list[x+]`

Lists all large objects in the database with their comments. `+` shows permissions.

### `\lo_unlink loid`

Deletes the large object with the specified OID.

---

## Output Formatting

### `\pset [ option [ value ] ]`

Sets options affecting query result table output. Without arguments, displays current settings.

| Option | Values | Description |
|--------|--------|-------------|
| `border` | 0-2 (3 for latex) | Border/line style. Higher = more lines. |
| `columns` | integer | Target width for wrapped format. 0 = use `COLUMNS` env or screen width. Non-zero also wraps output when sent to file or pipe (normally file/pipe output is unwrapped). |
| `csv_fieldsep` | character | CSV field separator (default: comma) |
| `expanded` (or `x`) | `on`, `off`, `auto` | Vertical display. `auto` uses expanded when wider than screen. Note: `auto` is only effective in `aligned` and `wrapped` formats. |
| `fieldsep` | string | Field separator for unaligned output (default: `\|`) |
| `fieldsep_zero` | — | Set field separator to NUL byte |
| `footer` | `on`, `off` | Toggle row count footer display |
| `format` | `aligned`, `asciidoc`, `csv`, `html`, `latex`, `latex-longtable`, `troff-ms`, `unaligned`, `wrapped` | Output format. See format descriptions below. |
| `linestyle` | `ascii`, `old-ascii`, `unicode` | Border character style. `ascii` uses `+`, `-`, `|` characters. `old-ascii` uses `:` and `;` for borders. `unicode` uses Unicode box-drawing characters. |
| `null` | string | Display string for NULL values (default: empty) |
| `numericlocale` | `on`, `off` | Locale-specific number formatting |
| `pager` | `on`, `off`, `always` | Pager control. Uses `PSQL_PAGER` or `PAGER` env. For `\watch` output, `PSQL_WATCH_PAGER` takes precedence over both. |
| `pager_min_lines` | integer | Minimum lines before pager activates (default: 0) |
| `recordsep` | string | Record separator for unaligned mode (default: newline) |
| `recordsep_zero` | — | Set record separator to NUL byte |
| `tableattr` (or `T`) | string | HTML: table tag attributes (e.g., `border=1`). latex-longtable: whitespace-separated proportional column widths (e.g., `'0.2 0.2 0.6'`). |
| `title` (or `C`) | string | Table title. Unset with no value. |
| `tuples_only` (or `t`) | `on`, `off` | Show only data, no headers/footers |
| `unicode_border_linestyle` | `single`, `double` | Unicode border drawing |
| `unicode_column_linestyle` | `single`, `double` | Unicode column drawing |
| `unicode_header_linestyle` | `single`, `double` | Unicode header drawing |
| `xheader_width` | `full`, `column`, `page`, or integer | Max width of expanded output header |

### Format Descriptions

| Format | Description |
|--------|-------------|
| `aligned` | Standard human-readable table with column alignment (default). |
| `wrapped` | Like `aligned` but long values wrap to fit column width. Headers with underscores are not repeated on continuation rows. |
| `unaligned` | All columns on one line, separated by `fieldsep`. Useful for script output. |
| `csv` | RFC 4180 compliant CSV output. Uses `csv_fieldsep` (default: comma). Safe for import into spreadsheets and other tools. |
| `html` | HTML `<table>` markup. |
| `asciidoc` | AsciiDoc table format for documentation. |
| `latex` | LaTeX tabular format. |
| `latex-longtable` | LaTeX longtable format for multi-page tables. Supports proportional column widths via `\pset tableattr` (e.g., `'0.2 0.2 0.6'`). |
| `troff-ms` | troff ms macros table format. |

### Formatting shortcuts

| Shortcut | Equivalent |
|----------|-----------|
| `\a` | `\pset format unaligned` (toggle) |
| `\C [title]` | `\pset title` |
| `\f [string]` | `\pset fieldsep` |
| `\H` | `\pset format html` (toggle) |
| `\t` | `\pset tuples_only` (toggle) |
| `\T table_options` | `\pset tableattr` |
| `\x [on\|off\|auto]` | `\pset expanded` |

---

## Scripting and Control Flow

### `\i` / `\include` filename

Reads and executes input from the file. Relative to current working directory. Use `-` for stdin.

**stdin behavior**: When using `\i -`, psql reads from standard input until EOF. Note that Readline editing is not available when reading from stdin. If `\i -` is used inside a file being processed (nested inclusion), it reads from the parent's input stream — use with caution in scripts.

### `\ir` / `\include_relative` filename

Like `\i`, but resolves relative paths from the directory of the currently executing script (not the working directory). Prefer `\ir` for portable scripts.

### `\o` / `\out [ filename ]` / `\o [ |command ]`

Redirects query output (tables, command responses, notices, `\d` output) to file or pipe. `\o` without arguments resets to stdout. When argument starts with `|`, the rest is passed literally to the shell (no variable interpolation).

Note: `\echo` goes to stdout (not affected by `\o`); use `\qecho` for redirected output.

### `\echo text [ ... ]`

Prints arguments to stdout, separated by spaces, followed by a newline. If first argument is unquoted `-n`, no trailing newline is written.

### `\qecho text [ ... ]`

Like `\echo` but outputs to the query output channel (set by `\o`).

### `\warn text [ ... ]`

Like `\echo` but outputs to stderr.

### `\set [ name [ value [ ... ] ] ]`

Sets a psql variable. Multiple values are concatenated. `\set` without arguments shows all variables. Variable names are case-sensitive, can contain letters, digits, underscores.

This is unrelated to the SQL `SET` command.

### `\unset name`

Unsets (deletes) a psql variable. Most control variables cannot be truly unset; they revert to defaults.

### `\prompt [ text ] name`

Prompts the user for input and stores it in the named variable. For multiword prompts, surround with single quotes.

**Behavior with `-f` flag**: When psql is invoked with `-f` (reading commands from a file), `\prompt` reads from stdin/stdout rather than the terminal. In interactive mode, it uses the terminal directly.

### `\getenv psql_var env_var`

Reads an environment variable and stores it in a psql variable. No change if the env var is undefined.

```sql
\getenv home HOME
\echo :home
-- outputs: /home/postgres
```

### `\setenv name [ value ]`

Sets or unsets an environment variable from within psql.

```sql
\setenv PAGER less
\setenv LESS -imx4F
```

### `\p` / `\print`

Prints the current query buffer to stdout. If the buffer is empty, prints the most recently executed query.

### `\w` / `\write` filename / `\w |command`

Writes the current query buffer to a file or pipes it to a shell command. If the buffer is empty, writes the most recently executed query. When argument starts with `|`, rest is passed literally to the shell.

### `\if` / `\elif` / `\else` / `\endif`

Nestable conditional blocks. `\if` and `\elif` evaluate their argument as a boolean (true/false/1/0/on/off/yes/no, case-insensitive). All backslash commands in a conditional block must appear in the same source file.

```sql
SELECT EXISTS(SELECT 1 FROM customer WHERE customer_id = 123) as is_customer,
       EXISTS(SELECT 1 FROM employee WHERE employee_id = 456) as is_employee
\gset
\if :is_customer
    SELECT * FROM customer WHERE customer_id = 123;
\elif :is_employee
    \echo 'is not a customer but is an employee'
    SELECT * FROM employee WHERE employee_id = 456;
\else
    \echo 'not a customer or employee'
\endif
```

Variable references in skipped lines are NOT expanded. Backquote expansion is NOT performed in skipped lines.

---

## Pipeline Mode

Pipeline mode batches SQL statements into fewer network round trips for better performance. Available in PostgreSQL 14+.

### Pipeline commands

| Command | Description |
|---------|-------------|
| `\startpipeline` | Begin a pipeline block |
| `\endpipeline` | End a pipeline block and process remaining results |
| `\sendpipeline` | Append current query buffer to pipeline without waiting for results |
| `\syncpipeline` | Send a sync message without ending the pipeline |
| `\flushrequest` | Request server flush without sync |
| `\flush` | Manually push unsent data to server |
| `\getresults [N]` | Read pending results (N=0 or omitted = all) |

### Pipeline rules

- All queries in pipeline mode use the extended query protocol
- Queries are appended with semicolons or `\sendpipeline`
- Allowed meta-commands: `\bind`, `\bind_named`, `\parse`, `\close_prepared`
- NOT allowed: `\g`, `\gx`, `\gdesc` (and other result-consuming commands)
- `COPY` is not supported in pipeline mode
- A `%P` prompt variable is available to show pipeline status (`on`, `off`, or `abort`)

### Example

```sql
\startpipeline
  SELECT * FROM pg_class;
  SELECT 1 \bind \sendpipeline
  \flushrequest
  \getresults
\endpipeline
```

---

## Session Management

### `\e` / `\edit [ filename ] [ line_number ]`

Opens the query buffer (or a file) in the external editor. On save, the buffer is re-parsed. Complete queries are immediately executed. The cursor is positioned on the specified line number. See `$EDITOR` / `$VISUAL` for editor configuration.

### `\ef [ function_description [ line_number ] ]`

Edits a function or procedure definition as a `CREATE OR REPLACE FUNCTION/PROCEDURE` command. Specify function by name or name and argument types. Without arguments, shows a blank template. Line number positions within the function body.

Unlike most meta-commands, the entire line is the argument — no variable interpolation.

### `\ev [ view_name [ line_number ] ]`

Edits a view definition as a `CREATE OR REPLACE VIEW` command. Without arguments, shows a blank template.

### `\cd [ directory ]`

Changes the current working directory. Without an argument, changes to the home directory.

```sql
\cd /tmp
\! pwd           -- /tmp
\cd              -- back to home directory
```

### `\r` / `\reset`

Clears the query buffer.

### `\s [ filename ]`

Prints command history to file or stdout. Requires Readline support.

### `\timing [ on | off ]`

Toggles (or explicitly sets) display of query execution time. Shown in milliseconds; intervals > 1s also show minutes:seconds, hours, days as needed.

### `\errverbose`

Repeats the most recent server error message at maximum verbosity (as if `VERBOSITY=verbose` and `SHOW_CONTEXT=always`).

### `\restrict restrict_key` / `\unrestrict restrict_key`

Enter/exit restricted mode where only `\unrestrict` is allowed. Key must be alphanumeric. Primarily used by `pg_dump`/`pg_restore`.

---

## Help and Information

### `\? [ topic ]`

Shows psql help. Topics:
- `commands` (default) — backslash commands
- `options` — command-line options
- `variables` — configuration variables

### `\h` / `\help [ command ]`

SQL syntax help. Without arguments, lists available commands. `*` shows help for all commands. Multi-word commands don't need quoting: `\h ALTER TABLE`.

Unlike most meta-commands, the entire line is the argument — no variable interpolation.
