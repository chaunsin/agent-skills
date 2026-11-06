# Architecture and Schema Migration

Read for service boundaries, tenancy, partitioning, sharding, replication, or production migrations. Justify architectural expansion with business, scale, or reliability needs.

## Service boundaries and tenants

A monolith may share an instance, but assign table ownership and write responsibility by domain. Microservices should own their data; other services should use APIs, events, or controlled synchronization rather than depend on internal tables or share writes. Evaluate outbox, saga, compensation, and eventual consistency for cross-service operations; do not assume cross-service joins or a single transaction.

Choose shared tables, separate schemas, or separate databases/clusters according to tenant scale, isolation, backup, and operating costs. For shared tables, identify every tenant-scoped table and the source of `tenant_id`; scope all reads, updates, and deletes; enforce tenant-scoped uniqueness; verify joined entities share a tenant; consider tenant indexes and partitions; and define authorization for jobs, administrators, and cross-tenant reporting.

## Partitioning and sharding

First consider modeling, indexes, query optimization, archiving, and cleanup. Consider native RANGE/LIST/HASH partitioning, horizontal tables, or separate databases only for a demonstrated maintenance, capacity, or throughput bottleneck.

Define partition or shard keys against query patterns, routing and rebalancing, global IDs, cross-shard queries and pagination, transactions and compensation, migration, backup, recovery, and operating costs. A primary key identifies a record; a shard key routes it. A Snowflake ID does not automatically yield balanced or query-appropriate routing. Partitioning is not sharding and partition pruning does not make every query faster; check uniqueness limitations, maintenance, routing, and actual plans.

## Replication and availability

Define writers, read replicas, replication mode and lag. Route read-after-write, transactional, and strongly consistent reads to a node with the required guarantee. Assess failover, split-brain protection, detection, data-loss window, recovery, and agreed RPO and RTO. High availability is not backup: maintain independent backups and exercise restoration. Multi-writer systems require conflict detection, merging, and uniqueness handling.

## Online migrations

Inspect existing data, callers, indexes, constraints, transactions, and deployment before changing production. Assess field removal, tighter constraints, and changed semantics before execution. For large tables or multiple application versions, evaluate expand and contract:

1. Expand with new fields, tables, or indexes while the old path works.
2. Deploy compatibility with both structures.
3. Backfill in retryable batches.
4. Check counts, uniqueness, relationships, precision, and business invariants.
5. Switch reads and writes and monitor.
6. Remove old structures only after old versions and the rollback window have passed.

Document locks, duration, failure handling, rollback or forward repair, backups, and monitoring. Validate counts and shard distribution, keys and references, business uniqueness, NULL/default/enum mappings, amounts and units, time zones and precision, application compatibility, rerun idempotency, failure recovery, and backup restoration.
