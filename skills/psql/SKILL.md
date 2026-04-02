---
name: psql
description: >
  PostgreSQL interactive terminal (psql) reference and usage guide. Use this skill whenever the user
  mentions psql, PostgreSQL command-line client, backslash commands, meta-commands, \d commands,
  database inspection, SQL scripting in PostgreSQL, importing/exporting data with psql, \copy,
  psql formatting, psql variables, or any task involving connecting to or interacting with a
  PostgreSQL database from the terminal. Also applies when the user asks about PostgreSQL query
  execution, table inspection, schema exploration, database administration from CLI, or psql
  configuration and customization. Even if the user doesn't explicitly say "psql" but is working
  with PostgreSQL from the command line, this skill is relevant.
---
# psql — PostgreSQL Interactive Terminal

psql is PostgreSQL's feature-rich interactive terminal. It lets you write and execute queries, inspect database objects, import/export data, script batch operations, and customize output formatting — all from the command line.

## Prerequisites

Before using psql, verify it is installed and available:

```bash
# Check if psql is installed
psql --version

# If not found, install PostgreSQL client tools:

# macOS (Homebrew)
brew install libpq
brew link --force libpq

# Ubuntu / Debian
sudo apt install postgresql-client

# CentOS / RHEL
sudo yum install postgresql

# Alpine
apk add postgresql-client

# Windows — install PostgreSQL via the official installer or use WSL
```

psql ships as part of the `postgresql-client` package. The server (`postgresql`) is not required — you only need the client to connect to a remote PostgreSQL instance.

## Quick Reference

### Connecting

```
# 1. CLI flags
psql -h host -p port -U user -d dbname

# 2. Connection URI
# WARNING: Password in URI is visible in shell history and process listings.
#          Prefer ~/.pgpass for production use (see method 4 below).
psql "postgresql://user:pass@host:port/dbname"

# 3. Environment variables (no flags needed)
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=mydb
export PGUSER=postgres
# WARNING: PGPASSWORD is visible in process listings (e.g. `ps aux`).
#          Use ~/.pgpass in production instead.
export PGPASSWORD=123456
psql                       # picks up all params from env

# 4. ~/.pgpass file (RECOMMENDED for passwords)
#    Format: hostname:port:database:username:password
echo "localhost:5432:mydb:postgres:123456" >> ~/.pgpass
chmod 600 ~/.pgpass
psql -h localhost -U postgres -d mydb   # no password prompt

# 5. Execute and exit
psql -f script.sql dbname                        # execute file then exit
psql -c "SELECT 1" dbname                        # run single command then exit
psql -1 -f migration.sql dbname                  # run in single transaction
```

Key flags: `-h` host, `-p` port, `-U` user, `-d` database, `-w` no password prompt, `-W` force password prompt.

**Precedence**: CLI flags > environment variables > ~/.pgpass > defaults. Use `~/.pgpass` instead of `PGPASSWORD` in production — `PGPASSWORD` is visible in process listings.

### Object Inspection (\d family)

| Command           | Shows                                                                                |
| ----------------- | ------------------------------------------------------------------------------------ |
| `\d`            | All tables, views, materialized views, sequences, foreign tables (equiv.`\dtvmsE`) |
| `\dP`           | Partitioned tables                                                                   |
| `\dt`           | Tables only                                                                          |
| `\dv`           | Views only                                                                           |
| `\di`           | Indexes only                                                                         |
| `\ds`           | Sequences only                                                                       |
| `\dm`           | Materialized views only                                                              |
| `\de`           | Foreign tables only                                                                  |
| `\dT`           | Data types                                                                           |
| `\df`           | Functions                                                                            |
| `\da`           | Aggregate functions                                                                  |
| `\dn`           | Schemas                                                                              |
| `\du` / `\dg` | Roles                                                                                |
| `\db`           | Tablespaces                                                                          |
| `\dc`           | Conversions                                                                          |
| `\dD`           | Domains                                                                              |
| `\dl`           | Large objects                                                                        |
| `\dF`           | Text search configurations                                                           |
| `\dFd`          | Text search dictionaries                                                             |
| `\dFp`          | Text search parsers                                                                  |
| `\dFt`          | Text search templates                                                                |
| `\des`          | Foreign servers                                                                      |
| `\deu`          | User mappings                                                                        |
| `\dew`          | Foreign-data wrappers                                                                |
| `\dp`           | Privileges (GRANT/REVOKE)                                                            |
| `\l`            | List databases                                                                       |

| `\dA`           | Access methods                                           |
| `\dAc` / `\dAf` / `\dAo` / `\dAp` | Operator classes, families, operators, support functions |
| `\dC`           | Type casts                                               |
| `\dconfig`      | Server configuration parameters                          |
| `\dd`           | Object descriptions (comments)                           |
| `\ddp`          | Default privileges                                       |
| `\dL`           | Procedural languages                                     |
| `\do`           | Operators                                                |
| `\dO`           | Collations                                               |
| `\dP[itn]`      | Partitioned tables (`t`=tables, `i`=indexes, `n`=nested) |
| `\drg`          | Granted role memberships                                 |
| `\dRp` / `\dRs` | Replication publications / subscriptions                 |
| `\dX`           | Extended statistics                                      |
| `\dx`           | Installed extensions                                     |
| `\dy`           | Event triggers                                           |
| `\sf[+]`        | Show function definition                                 |
| `\sv[+]`        | Show view definition                                     |
| `\z`            | Privileges (alias for `\dp`)                             |

**Modifiers** (append to most `\d` commands):

- `+` — extra info (size, description): `\dt+`, `\l+`, `\du+`
- `S` — include system objects: `\dtS`, `\dfS+`
- `x` — expanded display mode: `\dt+x` (note: `\dx` is a different command; `x` must follow `S` or `+`)

Provide a name for details: `\d table_name` shows columns, types, indexes, constraints, foreign keys.

**Pattern matching** in \d commands:

- `*` = any sequence of characters, `?` = single character
- `.` separates schema from object: `\dt public.*` or `\dt my_schema.users`
- `..` separates database.schema.object: `\dt mydb.public.*`
- Double quotes stop case folding and wildcard expansion: `\dt "FOO"` matches `FOO` not `foo`
- `$` is matched literally (not regex anchor)
- Regex chars like `[0-9]` work: `\dt user[0-9]*` matches `user1`, `user2`

### Query Execution

| Command               | Action                                                       |
| --------------------- | ------------------------------------------------------------ |
| `;`                 | Execute the current query buffer                             |
| `\g`                | Execute (like `;`, but can add options)                    |
| `\gx`               | Execute with expanded output (like `\g`, forces `\x on`) |
| `\g filename`       | Execute and send output to file                              |
| `\g \| command`      | Execute and pipe output to shell command                     |
| `\gdesc`            | Describe result columns without executing                    |
| `\gset [prefix]`    | Execute and store results in psql variables                  |
| `\gexec`            | Execute each cell of result as a SQL command                 |
| `\crosstabview`     | Display result as crosstab (pivot table)                     |
| `\watch`            | Re-execute query periodically (see below)                    |
| `\bind [params...]` | Use extended query protocol with parameters                  |
| `\;`                | Append semicolon to buffer without executing                 |

### Data Import/Export

```sql
-- Server-side (requires superuser for file access, uses server filesystem)
COPY table TO '/path/file.csv' WITH (FORMAT csv, HEADER true);
COPY table FROM '/path/file.csv' WITH (FORMAT csv, HEADER true);

-- Client-side (runs with client permissions, no superuser needed) — preferred
\copy table TO '/path/file.csv' WITH (FORMAT csv, HEADER true)
\copy table FROM '/path/file.csv' WITH (FORMAT csv, HEADER true)
\copy (SELECT ...) TO '/path/output.csv' WITH (FORMAT csv, HEADER true)
```

`\copy` is the go-to for day-to-day work — it uses the client's filesystem and permissions, not the server's.

**\copy syntax detail:**

```
-- FROM (import): sources are 'filename', program 'command', stdin, pstdin
\copy table FROM 'file.csv' WITH (FORMAT csv, HEADER true) [ WHERE condition ]

-- TO (export): destinations are 'filename', program 'command', stdout, pstdout
\copy table TO 'file.csv' WITH (FORMAT csv, HEADER true)
```

WARNING: The `program` option executes a shell command. If constructed from user input, it can lead to command injection. Avoid string concatenation with untrusted data.

### Output Formatting

```
\a                  Toggle aligned/unaligned output
\x                  Toggle expanded display (vertical vs table)
\t                  Toggle tuples only (no headers/footers)
\pset format FORMAT  Set output format: aligned, asciidoc, csv, html, latex, latex-longtable, troff-ms, unaligned, wrapped
\pset border N       Set border style (0-2)
\pset null STRING    Display NULL as STRING
\pset pager [off]    Control pager usage
\pset title 'TEXT'   Set table title
\pset recordsep SEP  Set record separator for unaligned mode
\H                   Toggle HTML output (shortcut)
```

### Scripting & Control Flow

```
\i filename         Execute file (relative to current working directory)
\ir filename        Execute file (relative to the script being processed)
\o [filename]       Redirect query output to file (or pipe with |cmd)
\o                   Stop output redirection
\qecho TEXT          Output text to redirected output
\echo TEXT           Output text to stdout
\warn TEXT           Output text to stderr
\! command           Execute shell command
\cd [dir]            Change working directory
\set NAME VALUE      Set psql variable
\unset NAME          Unset psql variable
\prompt [TEXT] NAME  Prompt user for variable value

-- Conditional execution (useful in scripts)
\if EXPR
  \echo 'true branch'
\else
  \echo 'false branch'
\endif

\elif EXPR           Else-if inside \if block
```

Variables in SQL: `:'varname'` (quoted string), `:'varname'::type` (with cast), `:varname` (unquoted).

### Session Management

```
\c [dbname [user]]  Connect to database (or reconnect)
\conninfo           Display connection info (includes SSL info)
\encoding [ENC]     Set or show client encoding
\password [USER]    Change password (does NOT appear in command history or server log)
\q                   Quit psql
\r                   Reset (clear) the query buffer
\e                   Edit query buffer in external editor
\ef [FUNCNAME]       Edit function definition
\ev [VIEWNAME]       Edit view definition
\sf[+] FUNCNAME      Show function definition (read-only)
\sv[+] VIEWNAME      Show view definition (read-only)
\s [FILE]            Print command history (or save to file)
\restrict KEY        Enter restricted mode (only \unrestrict allowed)
\unrestrict KEY      Exit restricted mode
```

### Pipeline Mode (PostgreSQL 14+)

```
\startpipeline
  \bind 42 \g
  \bind 100 \g
\endpipeline
```

Pipelines batch multiple queries into a single network round trip, reducing latency for many small queries.

**Pipeline limitations:**
- `COPY` is not supported in pipeline mode
- Meta-commands like `\g`, `\gx`, `\gdesc` are not allowed inside a pipeline
- All queries use the extended query protocol

**Advanced pipeline commands:**
- `\flushrequest` — request server flush without sync
- `\flush` — manually push unsent data to server
- `\getresults [N]` — read pending results (N=0 means all)

### \watch Syntax

```
\watch [i[nterval]=SECONDS] [c[ount]=TIMES] [m[in_rows]=ROWS] [SECONDS]
```

- `interval` — seconds between executions (default: 2, overridable via `WATCH_INTERVAL` variable)
- `count` — stop after N executions
- `min_rows` — stop if query returns fewer than N rows

Examples:
```sql
SELECT * FROM pg_stat_activity WHERE state = 'active';
\watch interval=5 count=10      -- every 5s, stop after 10 runs

SELECT count(*) FROM queue WHERE status = 'pending';
\watch i=1 min_rows=1            -- every 1s, stop when queue is empty
```

## Security Considerations

### Destructive Operations Checklist

Before running any destructive SQL, verify impact first:

```sql
-- BEFORE DELETE: check how many rows are affected
SELECT count(*) FROM users WHERE condition;  -- verify scope
BEGIN;
DELETE FROM users WHERE condition RETURNING *;  -- see what was deleted
-- ROLLBACK if wrong; COMMIT only after verification

-- BEFORE DROP TABLE: verify no foreign keys depend on it
\d table_name  -- check "Referenced by" section
-- Consider renaming first: ALTER TABLE old RENAME TO old_backup;
```

### Dangerous Commands Requiring Extra Caution

| Command/Pattern | Risk | Mitigation |
|-----------------|------|------------|
| `\gexec` | Executes generated SQL without confirmation | Always inspect the generating query first by running it without `\gexec`; set `ON_ERROR_STOP on` |
| `\! command` | Arbitrary shell execution | No sandboxing; commands run with psql user's full privileges |
| `\copy ... program 'cmd'` | Shell command injection if filename comes from user input | Never concatenate untrusted input into the `program` string |
| `\deu+` | May display remote user passwords | Avoid using `\deu+` in shared/piped output; use `\deu` without `+` |
| `DELETE`/`UPDATE` without `WHERE` | Affects every row in the table | Always use `WHERE`; wrap in `BEGIN`/`ROLLBACK` to preview |
| `DROP DATABASE/TABLE` | Irreversible data loss | Verify you're on the correct database with `\conninfo` first |

### Variable Interpolation Safety

psql variables are **plain text substitution**, not parameterized queries. This means:

```sql
-- UNSAFE: if :name contains "Robert'); DROP TABLE users;--" it will execute the injection
SELECT * FROM users WHERE name = :'name';

-- SAFER: use \prompt for interactive input (user sees what they typed)
\prompt 'Enter name: ' search_name
SELECT * FROM users WHERE name = :'search_name';

-- SAFEST: use \bind for programmatic parameter passing (truly parameterized)
SELECT * FROM users WHERE name = $1;
\bind 'Robert' \g
```

The `:'varname'` form (quoted) is always safer than `:varname` (unquoted), because unquoted substitution can break SQL syntax or enable injection.

## When to Use What

| Scenario                      | Recommended Command                                            |
| ----------------------------- | -------------------------------------------------------------- |
| Quick table inspection        | `\d table_name`                                              |
| List all tables in schema     | `\dt schema.*`                                               |
| Check indexes on a table      | `\di+ table_name*` or `\d table_name`                      |
| Export query to CSV           | `\copy (SELECT ...) TO 'file.csv' WITH (FORMAT csv, HEADER)` |
| Import CSV into table         | `\copy table FROM 'file.csv' WITH (FORMAT csv, HEADER)`      |
| Run migration script          | `psql -1 -f migration.sql dbname`                            |
| Watch a live query            | `SELECT ... \watch 5`                                        |
| Pivot query results           | `SELECT ... \crosstabview`                                   |
| Script with conditional logic | `\if :var ... \endif`                                        |
| Batch-insert many rows        | Use `\startpipeline` / `\endpipeline`                      |

## Reference Files

For detailed information beyond this quick reference, see:

- **`references/meta-commands.md`** — Complete meta-command reference with all options, arguments, and behavior details. Consult this when you need the full specification of any backslash command.
- **`references/cli-options-and-variables.md`** — All CLI flags, environment variables, and psql internal variables (AUTOCOMMIT, ON_ERROR_STOP, ECHO, etc.). Refer to this when configuring psql startup behavior or writing scripts that depend on variable state.
- **`references/tips-and-patterns.md`** — Practical workflows, pattern matching rules for \d commands, common scripting patterns, and best practices. Useful when translating a task into the right sequence of psql commands.

## External References

- [PostgreSQL Client Applications](https://www.postgresql.org/docs/current/app-psql.html)
- [Official PostgreSQL Documentation](https://www.postgresql.org/docs/current/index.html)
- [The SQL Language](https://www.postgresql.org/docs/current/sql.html)
- [SQL Syntax - The SQL Language](https://www.postgresql.org/docs/current/sql-syntax.html)
- [SQL Command](https://www.postgresql.org/docs/current/sql-commands.html)
- [PostgreSQL Wiki](https://wiki.postgresql.org/)
