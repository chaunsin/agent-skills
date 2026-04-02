# psql Tips, Patterns & Best Practices

Practical workflows and common patterns for getting the most out of psql.

## Table of Contents

- [Pattern Matching in \d Commands](#pattern-matching-in-d-commands)
- [Common Workflows](#common-workflows)
- [Scripting Patterns](#scripting-patterns)
- [Output for Scripts and Automation](#output-for-scripts-and-automation)
- [Performance Tips](#performance-tips)
- [Data Import/Export Patterns](#data-importexport-patterns)
- [Debugging and Introspection](#debugging-and-introspection)
- [Safety and Best Practices](#safety-and-best-practices)
- [Gotchas and Common Mistakes](#gotchas-and-common-mistakes)

---

## Pattern Matching in \d Commands

All `\d` commands that accept a pattern parameter use the same matching rules. Understanding these rules is key to efficient database exploration.

### Pattern Syntax

| Pattern | Meaning | Example |
|---------|---------|---------|
| `*` | Any sequence of characters | `\dt user*` matches `users`, `user_accounts` |
| `?` | Any single character | `\dt user?` matches `users` but not `user_accounts` |
| `.` | Separates schema from object | `\dt public.*` lists all tables in `public` |

### How Matching Works

1. **Dot notation**: If the pattern contains a dot, the part before the dot matches schema names, the part after matches object names. `\dt public.users` means schema=`public`, table=`users`.

2. **No dot**: Matches objects in schemas on the current `search_path`. `\dt users` finds `users` in any searchable schema.

3. **Wildcard expansion**: `*` and `?` are expanded into regular expressions:
   - `*` becomes `.*` (any characters)
   - `?` becomes `.` (one character)
   - All other characters are treated as regex literals

4. **Case sensitivity**: By default, matching is case-sensitive. PostgreSQL folds unquoted identifiers to lowercase, so `\dt Users` won't find a table created as `users`.

### Practical Examples

```sql
-- All tables in any schema containing "user"
\dt *.user*

-- All tables in the public schema
\dt public.*

-- All tables starting with "order" in any schema
\dt *.order*

-- Detail view of a specific table
\d+ public.users

-- All indexes on tables starting with "user"
\di user*

-- All functions in the public schema
\df public.*

-- All materialized views
\dm

-- Check table size and description
\dt+ public.*
```

---

## Common Workflows

### Exploring a New Database

```
-- Step 1: What databases exist?
\l

-- Step 2: Connect to one
\c mydb

-- Step 3: What schemas are there?
\dn

-- Step 4: What tables exist?
\dt

-- Step 5: What does this table look like?
\d users

-- Step 6: Any indexes?
\di

-- Step 7: Any views?
\dv

-- Step 8: What functions exist?
\df

-- Step 9: What extensions are installed?
\dx

-- Step 10: Check current settings
SHOW all;
```

### Understanding Table Structure

```
-- Basic structure: columns, types, nullable, defaults
\d table_name

-- Detailed: everything above plus indexes, constraints, triggers, storage info
\d+ table_name

-- Just the indexes
\di table_name*

-- Just the foreign keys (shown in \d output)
\d table_name
-- Look for "Foreign-key constraints" section

-- Column comments
\dS+ table_name  -- includes system columns

-- Storage details (toast, compression)
\d+ table_name
```

### Checking Query Performance

```
-- Enable timing
\timing on

-- See the execution plan
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';

-- See what the optimizer actually does
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) SELECT ...;

-- Check current activity
SELECT * FROM pg_stat_activity WHERE state = 'active';

-- Watch a query
SELECT pg_size_pretty(pg_database_size(current_database()));
\watch 60
```

### Managing Transactions Manually

```
\set AUTOCOMMIT off

BEGIN;
  UPDATE accounts SET balance = balance - 100 WHERE id = 1;
  UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;

\set AUTOCOMMIT on
```

---

## Scripting Patterns

### Safe Script Template

```sql
-- Always start with this in scripts
\set ON_ERROR_STOP on
\set VERBOSITY verbose

-- Optional: echo commands for debugging
\set ECHO all

-- Your migration or operations go here
BEGIN;

ALTER TABLE users ADD COLUMN IF NOT EXISTS phone varchar(20);

COMMIT;
```

### Conditional Execution

```sql
-- Only run in specific environments
\set env `echo $APP_ENV`

\if :env = 'production'
  \echo 'WARNING: Running on PRODUCTION'
  \prompt 'Type YES to continue: ' confirm
  \if :confirm != 'YES'
    \echo 'Aborted.'
    \q
  \endif
\endif
```

### Dynamic SQL with \gexec

```sql
-- Generate and execute ANALYZE for all tables
SELECT 'ANALYZE ' || schemaname || '.' || tablename
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema');
\gexec

-- Generate GRANT statements
SELECT 'GRANT SELECT ON ' || tablename || ' TO readonly;'
FROM pg_tables
WHERE schemaname = 'public';
\gexec

-- Create partition tables dynamically
SELECT 'CREATE TABLE measurements_' || to_char(d, 'YYYY_MM') ||
       ' PARTITION OF measurements FOR VALUES FROM (''' ||
       to_char(d, 'YYYY-MM-01') || ''') TO (''' ||
       to_char(d + interval '1 month', 'YYYY-MM-01') || ''');'
FROM generate_series('2024-01-01'::date, '2024-12-01'::date, '1 month') AS d;
\gexec
```

### Store and Reuse Results with \gset

```sql
-- Get table count and use it
SELECT count(*) as user_count FROM users;
\gset
\echo 'Total users: ' :user_count

-- Get max ID and use in next query
SELECT max(id) as max_id FROM orders;
\gset
SELECT * FROM orders WHERE id > :max_id - 10;

-- Prefix to avoid collisions
SELECT oid, relname FROM pg_class WHERE relname = 'users';
\gset pg_
\echo 'OID of users table: ' :pg_oid
```

### Include Other Scripts

```sql
-- Relative to current working directory
\i init/001_schema.sql
\i init/002_seed.sql
\i init/003_permissions.sql

-- Relative to this file's location (better for portability)
\ir ../shared/helpers.sql
```

### Loop Pattern (using shell)

```bash
# Not a psql feature, but a common pattern combining shell and psql
for table in users orders products; do
  psql -c "SELECT count(*) FROM $table" mydb
done
```

---

## Output for Scripts and Automation

### Machine-Readable Output

```bash
# CSV output
psql -A -F ',' -t -c "SELECT id, name FROM users" mydb

# TSV output
psql -A -F $'\t' -t -c "SELECT id, name FROM users" mydb

# Single value (no header, no border)
psql -A -t -c "SELECT count(*) FROM users" mydb

# JSON output (use PostgreSQL's JSON functions)
psql -A -t -c "SELECT json_agg(t) FROM (SELECT id, name FROM users) t" mydb

# NUL-separated (for xargs -0)
psql -A -0 -t -c "SELECT filename FROM files" mydb | xargs -0 rm
```

### In-Session Output Control

```sql
-- Quick CSV dump
\pset format csv
\o /tmp/output.csv
SELECT id, name, email FROM users;
\o
\pset format aligned

-- Using \g options (no need to change global settings)
SELECT * FROM users \g (format=csv, footer=off) /tmp/users.csv

-- Pipe to a command
SELECT pg_database_size(current_database()) \g | numfmt --to=iec

-- Unaligned for quick copy-paste
\a
\t on
SELECT string_agg(column_name, ', ') FROM information_schema.columns WHERE table_name = 'users';
\t off
\a
```

---

## Performance Tips

### Large Result Sets

```sql
-- Don't load entire result into memory
\set FETCH_COUNT 1000
SELECT * FROM billion_row_table;

-- Use \copy instead of COPY for client-side operations
\copy huge_table TO '/data/export.csv' WITH (FORMAT csv)
```

### Pipeline Mode for Batch Operations

Pipeline mode batches multiple queries into single network round trips:

```sql
\startpipeline
  INSERT INTO logs (msg) VALUES ('entry 1');
  \bind \g
  INSERT INTO logs (msg) VALUES ('entry 2');
  \bind \g
  INSERT INTO logs (msg) VALUES ('entry 3');
  \bind \g
\endpipeline
```

This sends all three INSERTs in one network round trip instead of three.

### Script Execution

```bash
# Run in a single transaction (faster, and all-or-nothing)
psql -1 -f migration.sql mydb

# Multiple files sequentially
psql -1 -f 001.sql -f 002.sql -f 003.sql mydb
```

---

## Data Import/Export Patterns

### CSV Import

```sql
-- Standard CSV import
\copy table_name FROM 'data.csv' WITH (FORMAT csv, HEADER true)

-- Custom delimiter
\copy table_name FROM 'data.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

-- Handle NULLs
\copy table_name FROM 'data.csv' WITH (FORMAT csv, HEADER true, NULL 'N/A')

-- Specific columns only
\copy table_name (col1, col2, col3) FROM 'partial.csv' WITH (FORMAT csv, HEADER true)
```

### CSV Export

```sql
-- Full table export
\copy table_name TO 'export.csv' WITH (FORMAT csv, HEADER true)

-- Query export
\copy (SELECT id, name, created_at FROM users WHERE active ORDER BY created_at DESC) TO 'active_users.csv' WITH (FORMAT csv, HEADER true)

-- Compressed export
\copy table_name TO 'program ''gzip > export.csv.gz''' WITH (FORMAT csv, HEADER true)

-- Import from compressed
\copy table_name FROM 'program ''gzip -dc import.csv.gz''' WITH (FORMAT csv, HEADER true)
```

### Database Migration Between Servers

```bash
# Dump and restore via pipe (no intermediate file)
pg_dump -Fc source_db | pg_restore -d target_db

# Schema-only dump
pg_dump --schema-only source_db | psql target_db

# Data-only with parallel jobs
pg_dump -j4 -Fd source_db -f /tmp/dump_dir
pg_restore -j4 -d target_db /tmp/dump_dir
```

---

## Debugging and Introspection

### See What psql Sends to the Server

```sql
-- Echo all SQL commands
\set ECHO queries

-- See the SQL behind \d commands (incredibly useful for learning)
\set ECHO_HIDDEN on

-- Or in noexec mode (show but don't execute)
\set ECHO_HIDDEN noexec

-- Now run any \d command to see its SQL
\dt
\d users
```

### Check Query Plans

```sql
-- Basic plan
EXPLAIN SELECT * FROM users WHERE email = 'test@example.com';

-- With actual execution time
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';

-- Detailed with buffer info
EXPLAIN (ANALYZE, BUFFERS, VERBOSE) SELECT ...;

-- JSON format for tooling
EXPLAIN (FORMAT JSON) SELECT ...;
```

### Lock Analysis

```sql
-- Current locks
SELECT * FROM pg_locks WHERE NOT granted;

-- Blocking queries
SELECT blocked.pid, blocked.query, blocking.pid, blocking.query
FROM pg_locks blocked
JOIN pg_locks blocking ON blocked.locktype = blocking.locktype
  AND blocked.database IS NOT DISTINCT FROM blocking.database
  AND blocked.relation IS NOT DISTINCT FROM blocking.relation
  AND blocked.page IS NOT DISTINCT FROM blocking.page
  AND blocked.tuple IS NOT DISTINCT FROM blocking.tuple
  AND blocked.virtualxid IS NOT DISTINCT FROM blocking.virtualxid
  AND blocked.transactionid IS NOT DISTINCT FROM blocking.transactionid
  AND blocked.classid IS NOT DISTINCT FROM blocking.classid
  AND blocked.objid IS NOT DISTINCT FROM blocking.objid
  AND blocked.objsubid IS NOT DISTINCT FROM blocking.objsubid
  AND blocked.pid != blocking.pid
  AND NOT blocked.granted AND blocking.granted
JOIN pg_stat_activity blocked ON blocked.pid = blocked.pid
JOIN pg_stat_activity blocking ON blocking.pid = blocking.pid;

-- Or use pg_blocking_pids (PostgreSQL 9.6+)
SELECT query, pg_blocking_pids(pid) as blocked_by
FROM pg_stat_activity
WHERE cardinality(pg_blocking_pids(pid)) > 0;
```

---

## Safety and Best Practices

### Always Set ON_ERROR_STOP in Scripts

Without `ON_ERROR_STOP`, a script continues even after errors, potentially leaving the database in an inconsistent state:

```sql
-- Top of every script
\set ON_ERROR_STOP on
```

### Use Single-Transaction Mode for Migrations

```bash
# -1 wraps everything in BEGIN...COMMIT
# On error, the entire migration rolls back
psql -1 -f migration.sql mydb
```

### Never Use PGPASSWORD in Scripts

```bash
# BAD: Password visible in process list, env vars
PGPASSWORD=secret psql -c "SELECT 1" mydb

# GOOD: Use ~/.pgpass
echo "localhost:5432:mydb:myuser:mysecret" >> ~/.pgpass
chmod 600 ~/.pgpass
psql -c "SELECT 1" mydb
```

### Preview Before Executing

```sql
-- See what a migration will do without running it
\set ECHO_HIDDEN noexec
\i migration.sql

-- Or use \gdesc to check result columns
SELECT * FROM complex_view \gdesc
```

### Use \copy Over COPY

`\copy` uses client permissions and filesystem. SQL `COPY` runs on the server and requires superuser or pg_read_server_files/pg_write_server_files roles.

```sql
-- BAD (requires server-side file access)
COPY users TO '/tmp/users.csv' WITH CSV HEADER;

-- GOOD (uses client-side file access)
\copy users TO '/tmp/users.csv' WITH CSV HEADER
```

---

## Gotchas and Common Mistakes

### Semicolons in \copy

`\copy` does NOT end with a semicolon. It's a meta-command:

```sql
-- CORRECT
\copy users TO '/tmp/users.csv' WITH CSV HEADER

-- WRONG (psql interprets the semicolon oddly)
\copy users TO '/tmp/users.csv' WITH CSV HEADER;
```

### Variable Substitution and SQL Injection

psql variables are simple text substitution. They are NOT parameterized queries:

```sql
-- This is string substitution, NOT safe parameterized SQL
\set name "Robert'); DROP TABLE students;--"
SELECT * FROM users WHERE name = :'name';  -- MAY be unsafe

-- For user input, use \prompt and validate
\prompt 'Enter name (alphanumeric only): ' search_name
SELECT * FROM users WHERE name = :'search_name';
```

### Transaction State After Error

After an error in a transaction block, all subsequent commands fail until ROLLBACK:

```sql
BEGIN;
INSERT INTO users (id) VALUES (1);
INSERT INTO users (id) VALUES ('bad');  -- ERROR
INSERT INTO users (id) VALUES (2);      -- Also fails!
COMMIT;                                  -- Also fails!
```

Use `ON_ERROR_ROLLBACK` to auto-savepoint:

```sql
\set ON_ERROR_ROLLBACK on
BEGIN;
INSERT INTO users (id) VALUES (1);
INSERT INTO users (id) VALUES ('bad');  -- ERROR, auto-rollback to savepoint
INSERT INTO users (id) VALUES (2);      -- This works now
COMMIT;
```

### Pattern Matching is Regex

The `*` and `?` in \d commands are converted to regex. Special regex characters like `.`, `+`, `[`, `]` are treated as literals BUT `*` and `?` have special meaning:

```sql
-- These work as expected
\dt user*
\dt user?

-- If your table name actually contains *, use regex escaping
\dt table.with.dots    -- dots are literal in pattern position
```

### Connection String vs CLI Arguments

```bash
# These are equivalent
psql -h localhost -p 5432 -U admin -d mydb
psql "postgresql://admin@localhost:5432/mydb"

# But you can't mix freely — URI overrides individual flags
psql -h otherhost "postgresql://admin@localhost:5432/mydb"  -- uses localhost, not otherhost
```

### \i vs \ir

- `\i filename` — resolves relative to the **current working directory** (where psql was started)
- `\ir filename` — resolves relative to the **currently executing script's directory**

For script portability, prefer `\ir`:

```sql
-- In /scripts/migrations/run_all.sql:
\ir 001_schema.sql    -- resolves to /scripts/migrations/001_schema.sql
\ir 002_data.sql      -- resolves to /scripts/migrations/002_data.sql
```

### \o and Query Output

`\o` redirects query output, not meta-command output:

```sql
\o /tmp/output.txt
SELECT * FROM users;     -- goes to file
\d users                 -- also goes to file
\echo 'hello'            -- goes to STDOUT (not affected by \o)
\qecho 'hello'           -- goes to /tmp/output.txt (affected by \o)
```
