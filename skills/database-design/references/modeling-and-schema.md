# Modeling and Schema

Identify entities, responsibilities, ownership, and lifecycles first. Use third normal form as a baseline; denormalize only for a demonstrated need such as historical snapshots or measured reporting bottlenecks, documenting the authoritative source, synchronization, inconsistency window, and repair. Do not mechanically split tables or duplicate facts to avoid joins. Separate differing responsibilities, lifecycles, or permissions; justify hot/cold separation.

## Names and fields

Use consistent lowercase ASCII `snake_case`, avoiding reserved words, ambiguous abbreviations, and meaningless core names. Use domain prefixes where useful; do not repeat the table name in every field. Prefer a project's existing conventions.

Entity tables commonly have an `id` and `created_at`; use `updated_at` for mutable entities requiring change tracking, `deleted_at` only for required soft deletion, and `version` only for optimistic locking. Association tables can use composite keys; immutable events and ledgers generally do not need `updated_at`. Arrange fields for readability, not presumed performance.

Select integer ranges and text lengths from business bounds. Use `CHAR` only for truly fixed-length values; use `DECIMAL`/`NUMERIC` or integer minor units for money, with explicit currency, precision, and units. Use semantic booleans and native date/time types. JSON suits flexible attributes, not core relationships or frequently filtered fields. Match related types, signedness, precision, character sets, and collations.

Distinguish dates, instants, and durations. Use consistent UTC semantics for instants and explicit precision and conversion rules; do not rely on implicit server or session time zones. Define whether the application or database maintains timestamps and check ORM behavior. Calendar rules such as 09:00 local time may also require an IANA time-zone identifier.

Prefer `NOT NULL` where business semantics support it; define what NULL means and distinguish it from zero, empty strings, and unset values. Defaults must reflect business rules. Table and column comments should explain meaning, units, ranges, enums, and special conventions.

## Relationships and integrity

- One-to-one: use a shared primary key or unique reference; split only for meaningful lifecycle, access, security, update, or responsibility differences.
- One-to-many: put the reference on the many side; assess foreign keys and indexes.
- Many-to-many: use a join table with a composite key or an independent key plus a composite unique constraint; model independent attributes and lifecycle explicitly.
- Polymorphism: consider a common identity table plus typed extensions, a `type + id` reference with transactional validation, deletion protection and reconciliation, or separate association tables. A normal foreign key cannot enforce `type + id` across target tables. Do not choose polymorphism merely to reduce NULLs.

Use primary keys, uniqueness, NOT NULL, and supported CHECK constraints for invariants. Prefer physical foreign keys within a shared integrity boundary; when sharding, service boundaries, or proven operational constraints prevent them, define logical validation and repair. Choose `RESTRICT`, `NO ACTION`, `CASCADE`, or `SET NULL` by business semantics. For soft deletion define filtering, uniqueness, restoration, and eventual physical cleanup.

Classify rows in one table only when structure, lifecycle, and behavior align. Define stable finite status codes centrally; consider dictionary tables for dynamic values. Use bitmasks only for limited independent flags with documented bits and compatibility; use association tables for dynamic, queryable, or attributed selections.

Review missing entities, duplicated facts, cardinality, uniqueness scope, polymorphic integrity, NULL/default semantics, and lifecycle boundaries.
