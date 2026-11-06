# MySQL 物理设计参考

本文件用于目标数据库为 MySQL 时读取。生成 DDL 前应确认 MySQL 具体版本、存储引擎、字符集、排序规则、SQL mode 和时区配置。以下以 InnoDB 为常见业务默认，不代表所有部署必须采用相同参数。

## 1. 主键与整数

- 常规实体主键可评估 `BIGINT UNSIGNED AUTO_INCREMENT`。
- 若需与 PostgreSQL 等数据库共享同一逻辑 ID 范围，优先约定不超过有符号 BIGINT 上限的正整数，并使用兼容类型。
- `UNSIGNED` 增加正数范围，但会影响算术表达式及跨数据库兼容；不要在未考虑迁移需求时盲目使用。
- `AUTO_INCREMENT` 值可能有间隙，不具备业务连续编号语义。

示例：

```sql
CREATE TABLE lottery (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
    name VARCHAR(128) NOT NULL COMMENT '抽奖活动名称',
    status SMALLINT NOT NULL DEFAULT 0 COMMENT '活动状态：0-未开始，1-进行中，2-已结束',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间，按 UTC 语义存储',
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '最后修改时间，按 UTC 语义存储',
    PRIMARY KEY (id),
    KEY idx_lottery_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='抽奖活动表';
```

该示例假定应用和数据库连接统一以 UTC 解释 DATETIME 值；若项目采用其他维护策略，必须保持一致。

## 2. InnoDB 主键与索引

- InnoDB 使用聚簇索引组织行数据，通常以主键作为聚簇索引。
- 二级索引记录会包含主键值，因此主键过宽会增加二级索引存储成本。
- 优先为表定义稳定、短且唯一的主键；常规场景可使用 BIGINT。
- 趋势递增键通常有利于插入局部性，但高并发右端写入、页分裂及其他锁争用仍需实际测量。
- 如果未定义主键，InnoDB 可能选择合适的唯一非空索引或生成隐藏聚簇索引；业务表不应依赖隐藏主键。

## 3. 时间与时区

- `TIMESTAMP` 会根据会话时区在存储和读取时进行转换，并且存在范围限制。
- `DATETIME` 不执行相同的时区转换；如果用于时间点，应由应用和数据库连接统一约定按 UTC 写入和解释。
- `DATETIME(6)` / `TIMESTAMP(6)` 可表达微秒精度，精度应在项目内统一。
- `DATE` 只表达日历日期，不应替代时间点。
- 对“当地时间每天 09:00”等业务，保存 IANA 时区标识，不能只存 UTC 时间点。
- 自动更新时间可用默认值与 `ON UPDATE`，也可以由应用维护；一个项目应统一责任方并确认 ORM 行为。

## 4. 数据类型与约束

- 精确金额用 `DECIMAL(p,s)`；不要用 FLOAT/DOUBLE 记账。
- 文本长度按业务边界设计，不要统一使用 `VARCHAR(255)`。
- JSON 用于确有灵活结构需求的属性，不代替关联表。
- 检查约束、生成列、函数索引、在线 DDL 等能力需要按 MySQL 版本核实。
- 外键仅用于同一数据库完整性边界内且运维策略允许的关系；若不使用，需有应用层完整性方案。

## 5. 索引和 DDL 风险

- 联合 B-Tree 索引按查询条件、排序及数据分布设计，重点检查前导列。
- 评估唯一索引中的 NULL 语义、软删除数据的唯一性及字符排序规则。
- 大表建索引、改列、加约束前，确认目标版本的在线 DDL 能力、锁行为、重建成本及复制影响。
- 使用 `EXPLAIN` 查看计划；`EXPLAIN ANALYZE` 会执行语句，修改型语句须谨慎。

## 6. 官方文档

使用匹配部署版本的手册，下列链接对应文中 MySQL 8.4 行为。

- [InnoDB 聚簇与二级索引](https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html)
- [自增处理](https://dev.mysql.com/doc/refman/8.4/en/innodb-auto-increment-handling.html)
- [数值类型及无符号属性](https://dev.mysql.com/doc/refman/8.4/en/numeric-type-syntax.html)
- [InnoDB 表设计](https://dev.mysql.com/doc/refman/8.4/en/using-innodb-tables.html)
- [分区限制](https://dev.mysql.com/doc/refman/8.4/en/partitioning-limitations.html)
- [分区键与唯一键](https://dev.mysql.com/doc/refman/8.4/en/partitioning-limitations-partitioning-keys-unique-keys.html)

实际项目必须查看与部署版本一致的官方手册，不要默认使用此处示例所对应的版本能力。
