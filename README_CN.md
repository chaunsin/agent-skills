# Agent Skills

[English](README.md)

AI agent 技能集合 — 可被 AI 编程助手（如 Claude Code、Copilot CLI、Cursor）加载的独立知识库，用于在特定领域提供专业级辅助。

## 什么是 Skill？

Skill 是带有 YAML frontmatter 的结构化 Markdown 文档，作为特定主题的综合参考。AI agent 加载 skill 后可以在无需实时搜索文档的情况下，提供更准确、更具上下文感知的协助。

每个 skill 位于 `skills/<name>/` 目录下，包含：

- **`SKILL.md`** — 入口文件，包含 frontmatter 元数据和快速参考指南
- **`references/`** — 模块化的深入文件，涵盖详细语法、边缘情况和工作流

## 可用 Skills

| Skill                            | 说明                                                                                                                                                     |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [drizzle-migration-conflict][drizzle-migration-conflict] | Drizzle Kit 迁移冲突诊断与团队协作工作流 —— 检查 `_journal.json`、snapshot、迁移目录、merge conflict、`drizzle-kit check` 与 CI 预防方案 |
| [hugo-to-markdown][hugo-to-markdown] | Hugo 文档与内容转换参考 —— 检查本地 Hugo 配置、shortcode、render hook、front matter 和挂载内容根，生成安全的标准 Markdown 导出                             |
| [postgresql-cli][postgresql-cli] | [PostgreSQL](https://www.postgresql.org/docs/current/app-psql.html) 交互式终端 (psql) 参考 — 元命令、CLI 选项、格式化、数据导入/导出、脚本编写及高级工作流 |
| [pre-release-review][pre-release-review] | 生产上线前代码审查与发布就绪度审计 —— 检查 PR 或 git 范围中是否遗漏迁移、配置、缓存、队列、物料、密钥、安全、服务顺序和回滚风险 |
| [rclone-cli][rclone-cli]         | [Rclone](https://rclone.org/) 云存储管理器参考 — 终端中的上传、下载、同步、复制、移动、挂载、备份、过滤、加密、双向同步及多云远程管理                         |
| [redis-cli][redis-cli]           | [Redis](https://redis.io/docs/latest/develop/tools/cli/) 命令行界面参考 — Redis 查询、keyspace 检查、监控、延迟分析、ACL 与集群管理、脚本编写及模块工作流      |

## 安装

### npx skills（推荐）

[skills CLI](https://github.com/vercel-labs/skills) 是一个通用安装工具，支持 Claude Code、Cursor、Copilot、Codex 等 40 多种 agent。

```bash
# 安装本仓库所有 skills
npx skills add chaunsin/agent-skills

# 安装指定 skill
npx skills add chaunsin/agent-skills --skill postgresql-cli

# 安装前先查看可用 skills
npx skills add chaunsin/agent-skills --list

# 全局安装（所有项目可用）
npx skills add chaunsin/agent-skills -g

# 安装到指定 agent
npx skills add chaunsin/agent-skills -a claude-code -a cursor

# 检查已安装的 skills 是否有更新
npx skills check

# 更新所有已安装 skills 到最新版本
npx skills update

# 列出所有已安装的 skills（项目 + 全局）
npx skills list

# 移除指定 skill
npx skills remove postgresql-cli
```

### 手动安装

```bash
# 复制 skill 到 Claude Code skills 目录
cp -r skills/<skill-name> ~/.claude/skills/
```

## 使用方法

安装后，skill 会根据其触发关键词（定义在 `description` frontmatter 字段中）自动激活，无需手动配置。当你提出与 skill 领域相关的问题时，agent 会自动加载相应参考。

例如，安装 postgresql-cli skill 后，询问 "how to list all tables in psql" 或 "psql \d 命令" 即会触发该 skill。

## 仓库结构

```text
agent-skills/
├── skills/                  # Skill 目录
│   ├── drizzle-migration-conflict/ # Drizzle Kit 迁移冲突处理与预防
│   │   ├── SKILL.md         # Skill 入口文件
│   │   ├── references/      # 冲突处理、CI 策略、报告模板和来源链接
│   │   └── scripts/         # 只读迁移结构检查脚本
│   ├── postgresql-cli/      # PostgreSQL 交互式终端 (psql)
│   │   ├── SKILL.md         # Skill 入口文件
│   │   └── references/      # 详细参考文件
│   ├── pre-release-review/  # 生产发布就绪度审查
│   │   ├── SKILL.md         # Skill 入口文件
│   │   └── references/      # 检查清单与报告模板
│   ├── hugo-to-markdown/    # Hugo 文档和内容转标准 Markdown
│   │   ├── SKILL.md         # Skill 入口文件
│   │   ├── references/      # Hugo 转换规则
│   │   └── scripts/         # 规则盘点和校验脚本
│   ├── rclone-cli/          # Rclone 云存储管理器
│   │   ├── SKILL.md         # Skill 入口文件
│   │   ├── references/      # 详细参考文件
│   │   └── scripts/         # 辅助脚本
│   └── redis-cli/           # Redis 命令行界面
│       ├── SKILL.md         # Skill 入口文件
│       └── references/      # 详细参考文件
├── CLAUDE.md                # Claude Code 工作区指令
├── LICENSE                  # Apache 2.0 许可证
└── README.md                # 英文说明文件
```

## 许可证

[Apache License 2.0](LICENSE)

[postgresql-cli]: skills/postgresql-cli/SKILL.md
[drizzle-migration-conflict]: skills/drizzle-migration-conflict/SKILL.md
[hugo-to-markdown]: skills/hugo-to-markdown/SKILL.md
[pre-release-review]: skills/pre-release-review/SKILL.md
[rclone-cli]: skills/rclone-cli/SKILL.md
[redis-cli]: skills/redis-cli/SKILL.md
