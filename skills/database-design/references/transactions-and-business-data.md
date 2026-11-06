# Transactions, Concurrency, and Financial Data

Define atomic transaction boundaries, isolation, read/write order, commit, rollback, and retries. Keep transactions short and avoid uncontrolled external calls or long IO inside them. Sequential application SQL is not automatically atomic. For cross-service or cross-database consistency, assess outbox, saga, compensation, or eventual consistency.

## Concurrency and UPSERT

Choose controls for the conflict rate and business invariant: narrow lock scope and duration; optimistic version or old-value checks with affected-row verification; pessimistic locking where serialization is needed; atomic conditional updates such as `UPDATE ... SET stock = stock - 1 WHERE id = ? AND stock > 0`; unique constraints; and idempotency keys backed by uniqueness.

For create-or-update by a business key, assess native atomic UPSERT instead of check-then-insert. Define the conflict key and uniqueness constraint, and update only explicitly permitted fields; do not blindly overwrite states, amounts, creation times, or authoritative data. Use database expressions for atomic increments. Define timeouts, deadlock handling, bounded retries, backoff, and idempotency. Deduplicate batch conflict keys and define merge semantics. UPSERT does not replace transactions, cross-row invariants, conditional state transitions, or concurrency testing; performance depends on workload.

MySQL `INSERT ... ON DUPLICATE KEY UPDATE` can react to any primary or unique key, so assess multiple unique keys and their potentially different matching rows. Affected-row counts vary by insert, update, unchanged values, and client options. PostgreSQL `INSERT ... ON CONFLICT (key) DO UPDATE` needs an explicit conflict target; duplicate input keys affecting the same row can cause a cardinality violation. Verify atomicity, locking, return values, and isolation for other databases rather than assuming similar syntax has identical semantics.

Use triggers sparingly for database-wide integrity or audit rules, not hidden complex workflows or external calls. Document timing, tables, transaction behavior, recursion, deployment, rollback, and tests. Choose one consistent owner for `updated_at`.

## Money, assets, and inventory

Use `DECIMAL`/`NUMERIC` or integers in defined minor units, never floating point for exact accounting. Define currency, precision, rounding, exchange-rate basis, units, and whether balances, stock, or points may be negative, frozen, reserved, released, or expired.

Model asset identities, type-specific attributes, accounts, transactions, and orders by responsibility. Prefer append-only immutable ledger entries; correct history through reversals or adjustments. Define unique business transaction IDs, scoped idempotency keys, the authoritative balance source, and balance-to-ledger reconciliation. A version field does not replace a ledger, transaction, idempotency, or reconciliation. If using polymorphic `type + id`, define integrity validation, deletion protection, compensation, and reconciliation.

Use atomic conditional updates or suitable locks for inventory, issuance, redemption, and points. Enforce business uniqueness, valid state transitions, and timeout compensation for reservation/confirmation/release. Record actor, source, order or request ID, and event time for audit.

For financial or asset designs, report precision, authoritative data, transaction boundaries, concurrency controls, idempotency, uniqueness, immutable ledger policy, and reconciliation and repair. Mark unknown rules for confirmation.
