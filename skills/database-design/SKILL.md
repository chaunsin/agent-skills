---
name: database-design
description: Design and review relational database models and schemas for MySQL, PostgreSQL, and other relational databases. Use for domain modeling, tables and fields, primary and distributed IDs, constraints, indexes, concurrency, database architecture, DDL, and schema migrations.
metadata:
  author: chaunsin
  version: "0.1"
---

# Relational Database Design

Turn business requirements into maintainable relational models and physical schemas. Confirm the target database, version, storage engine, conventions, deployment, and migration tools before choosing physical syntax. Mark unknowns and assumptions; do not invent business rules.

## Principles

- Model entities, ownership, relationships, states, and lifecycles before writing DDL. Use third normal form as a baseline; justify denormalization and explain its source, synchronization, and consistency.
- Express integrity with primary keys, uniqueness, NOT NULL, checks, and suitable foreign keys. If physical foreign keys are unavailable, define application validation, transactions, compensation, or reconciliation.
- Keep distinct responsibilities and lifecycles separate. Use consistent lower-case ASCII `snake_case` names and avoid reserved words.
- Choose types, precision, nullability, and defaults from business semantics. Never use floating point for exact accounting.
- Design indexes for actual queries, ordering, joins, distributions, and plans. Avoid speculative redundancy, partitioning, sharding, or caches.

## Workflow

1. Identify entities, ownership, relationships, uniqueness, state transitions, access patterns, concurrency, retention, and security requirements.
2. Build the logical model and identify authoritative data and lifecycle boundaries.
3. Design tables, fields, keys, constraints, relationships, comments, and defaults. For a single writer, evaluate a numeric identity by default; evaluate distributed IDs only when needed.
4. Derive indexes from actual or expected SQL. Address soft deletion, optimistic locking, ledgers, tenancy, partitioning, replication, and high availability only where applicable.
5. Generate DDL for the confirmed database and version; review compatibility, integrity, concurrency, and migration risks.
6. Validate against the target database when possible. Otherwise report static review only and identify unverified SQL and assumptions.

## References

Read only the references relevant to the task; combine them when needed:

| Topic | Reference |
| --- | --- |
| Entities, normalization, fields, relationships, NULL, constraints, soft deletion | [Modeling and schema](references/modeling-and-schema.md) |
| Primary keys, identities, Snowflake, UUIDv7, shard keys | [ID strategy](references/id-strategy.md) |
| MySQL types, InnoDB, time, indexes, version differences | [MySQL](references/mysql.md) |
| PostgreSQL types, identity, UUID, time, indexes, version differences | [PostgreSQL](references/postgresql.md) |
| Indexes, query plans, pagination, IN and EXISTS | [Indexing and queries](references/indexing-and-query.md) |
| Transactions, concurrency, UPSERT, idempotency, money and ledgers | [Transactions and business data](references/transactions-and-business-data.md) |
| Service boundaries, tenants, partitioning, sharding, replication, migrations | [Architecture and migration](references/architecture-and-migration.md) |

For an ordinary single-database schema, start with modeling, ID strategy, and the target database reference.

## Deliver and review

As appropriate to the task, provide requirements and assumptions, entity boundaries and relationships, a table list and data dictionary, constraints and index rationale, version-compatible DDL with comments, and integrity, concurrency, performance, and migration risks. Clearly identify unresolved business decisions.

Review entity cardinality and lifecycle; naming; types, precision, units, nullability and defaults; compatible key types; uniqueness and referential integrity; soft-delete and recovery behavior; query-driven indexes; time zones and precision; transactions, idempotency and concurrency; tenant isolation and routing; and database-version compatibility. Do not present an unexecuted migration or SQL as validated.
