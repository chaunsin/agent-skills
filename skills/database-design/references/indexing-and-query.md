# Indexing and Query Design

Design indexes for real or explicitly expected queries, including filters, joins, ordering, grouping, ranges, pagination, and uniqueness. Balance reads against storage and write maintenance; do not impose a fixed index count. Review redundant and low-value indexes, data distribution and selectivity, and whether foreign-key columns need indexes in the target database.

Use the project's naming convention; otherwise consider `pk_<table>`, `uk_<table>_<columns>`, `idx_<table>_<columns>`, `fk_<table>_<ref>`, and `chk_<table>_<purpose>` within identifier limits. Do not rebuild equivalent objects merely to rename them.

For composite B-tree indexes, equality columns before range columns can be a starting point, with ordering and covering needs considered, but validate against actual plans, distribution, and database version. Leading-column rules and optimizations such as PostgreSQL skip scan vary. Avoid speculative wide indexes and every possible predicate permutation.

Specify the scope of business uniqueness and database-specific NULL behavior. For soft deletion, decide whether deleted rows release unique values; assess partial unique indexes or suitable generated-column strategies. Appending `deleted_at` to a unique index does not automatically enforce the desired rule. Use constraints for concurrent uniqueness rather than check-then-insert.

Use MySQL `EXPLAIN` or PostgreSQL `EXPLAIN`; where safe, use `EXPLAIN ANALYZE` or `EXPLAIN (ANALYZE, BUFFERS)`. Compare actual and estimated rows, scans, joins, sorts, temporary structures, row lookups, and buffer activity. ANALYZE executes the statement, so use a safe, rollback-capable environment for writes or side effects.

Choose `IN`, `EXISTS`, and `JOIN` by semantics, NULL behavior, data, indexes, and plans, not slogans. A NULL in `NOT IN` can yield surprising results; consider `NOT EXISTS`. Avoid unnecessary `SELECT *`, N+1 queries, implicit conversions, functions on indexed columns, and needless joins. For deep pagination evaluate keyset pagination with a unique tie-breaker. Size batches with parameter limits, transactions, locks, and retries in mind.

For important indexes explain the query, column order, expected benefit, and write cost. Without measured plans, label performance claims as design estimates.
