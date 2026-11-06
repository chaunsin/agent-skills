# MySQL Physical Design

Confirm the MySQL version, engine, character set, collation, SQL mode, and time zone before generating DDL. InnoDB is a common default, not a universal requirement.

Evaluate `BIGINT UNSIGNED AUTO_INCREMENT` for ordinary entity IDs; use a signed-compatible positive range when sharing a logical ID range with PostgreSQL. Unsigned arithmetic and portability need consideration. Auto-increment values can have gaps.

```sql
CREATE TABLE lottery (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
    name VARCHAR(128) NOT NULL COMMENT 'Lottery name',
    status SMALLINT NOT NULL DEFAULT 0 COMMENT 'Status: 0 pending, 1 active, 2 ended',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Creation time in UTC',
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6) COMMENT 'Last update in UTC',
    PRIMARY KEY (id), KEY idx_lottery_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Lottery';
```

This example assumes application and connections consistently interpret `DATETIME` as UTC. InnoDB generally clusters rows by primary key and includes that key in secondary indexes; wide keys increase cost. Ordered keys can improve locality but contention and page splits require measurement. Do not rely on a hidden clustered key for business tables.

`TIMESTAMP` converts using the session time zone and has range limits; `DATETIME` does not perform the same conversion. Standardize UTC interpretation and precision, and store an IANA zone for local calendar rules. Decide consistently whether the application or `ON UPDATE` maintains timestamps and verify ORM behavior.

Use `DECIMAL` for exact money; choose text lengths by domain; use JSON for flexible attributes rather than relationships. Verify CHECK, generated columns, functional indexes, and online DDL against the version. If foreign keys are omitted, define integrity enforcement. Assess composite indexes, NULL and soft-delete uniqueness, and collation. Before large-table DDL assess locks, rebuild cost, and replication. `EXPLAIN ANALYZE` executes statements.

Use the manual for the deployed version. These links describe MySQL 8.4: [clustered and secondary indexes](https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html), [auto-increment](https://dev.mysql.com/doc/refman/8.4/en/innodb-auto-increment-handling.html), [numeric types](https://dev.mysql.com/doc/refman/8.4/en/numeric-type-syntax.html), [InnoDB table design](https://dev.mysql.com/doc/refman/8.4/en/using-innodb-tables.html), [partition restrictions](https://dev.mysql.com/doc/refman/8.4/en/partitioning-limitations.html), and [partition and unique keys](https://dev.mysql.com/doc/refman/8.4/en/partitioning-limitations-partitioning-keys-unique-keys.html).
