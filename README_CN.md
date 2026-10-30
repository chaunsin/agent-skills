# Agent Skills

[English](README.md)

AI agent 技能集合 — 可被 AI 编程助手（如 Claude Code、Copilot CLI、Cursor）加载的独立知识库，用于在特定领域提供专业级辅助。

## 什么是 Skill？

Skill 是一个包含 `SKILL.md` 入口文件和可选辅助资源的目录，为 agent 提供可复用的任务指导和领域知识，并按需加载详细内容。

每个 skill 位于 `skills/<name>/` 目录下，包含：

- **`SKILL.md`** — 入口文件，包含 frontmatter 元数据和快速参考指南
- **辅助 Markdown 文档**（可选）— 详细语法、边缘情况、工作流或模板，位于 `references/`、`reference/` 或与 `SKILL.md` 同级的文件中
- **`scripts/`**（可选）— 用于验证、盘点或安装的辅助脚本
- **`assets/`**（可选）— 用于生成结果的模板及其他资源
- **`agents/`**（可选）— 智能体专用配置与界面元数据

## 可用 Skills

| Skill                            | 说明                                                                                                                                                     |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [drizzle-migration-conflict][drizzle-migration-conflict] | Drizzle Kit 迁移冲突诊断与团队协作工作流 —— 检查 `_journal.json`、snapshot、迁移目录、merge conflict、`drizzle-kit check` 与 CI 预防方案 |
| [git-stack][git-stack] | Git 工作流 —— 提交与推送更改、处理合并或变基冲突、创建或复用 worktree，明确操作范围并复用有效验证结果 |
| [grill][grill] | 决策访谈 —— 通过逐轮追问检验计划、想法或设计，用设计树梳理决策依赖，澄清假设并达成共识 |
| [hugo-to-markdown][hugo-to-markdown] | Hugo 文档与内容转换参考 —— 检查本地 Hugo 配置、shortcode、render hook、front matter 和挂载内容根，生成安全的标准 Markdown 导出                             |
| [postgresql-cli][postgresql-cli] | [PostgreSQL](https://www.postgresql.org/docs/current/app-psql.html) 交互式终端 (psql) 参考 — 元命令、CLI 选项、格式化、数据导入/导出、脚本编写及高级工作流 |
| [prd][prd] | 产品需求生成 —— 将想法与澄清后的需求整理为 PRD，在实施前明确目标用户、业务目标、范围、行为和验收标准 |
| [pre-release-review][pre-release-review] | 生产上线前代码审查与发布就绪度审计 —— 检查 PR 或 git 范围中是否遗漏迁移、配置、缓存、队列、物料、密钥、安全、服务顺序和回滚风险 |
| [rclone-cli][rclone-cli]         | [Rclone](https://rclone.org/) 云存储管理器参考 — 终端中的上传、下载、同步、复制、移动、挂载、备份、过滤、加密、双向同步及多云远程管理                         |
| [redis-cli][redis-cli]           | [Redis](https://redis.io/docs/latest/develop/tools/cli/) 命令行界面参考 — Redis 查询、keyspace 检查、监控、延迟分析、ACL 与集群管理、脚本编写及模块工作流      |
| [to-spec][to-spec] | 技术规格生成 —— 默认使用 PRD 内容，也支持用户明确提供或指定的 ADR、访谈、QA 文档，保留来源追溯并明确实施契约和验证标准 |
| [to-task][to-task] | 任务拆解 —— 生成依赖与验收明确的任务计划；保存前询问记录方式，默认在本地按功能分目录、每个任务一份 Markdown，也支持 GitHub/GitLab Issues 及用户明确指定的可用任务系统 |

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

规划工作时，可以用 `grill` 盘问未明确的决策，用 `prd` 定义产品需求，用 `to-spec` 明确技术契约，用 `to-task` 生成可验证的任务计划。按当前需要选择技能，无需依次执行全部流程；`to-spec` 默认接收 PRD 内容，也支持明确提供或指定的其他来源。需要提交、推送、解决冲突或准备 worktree 时，使用 `git-stack`。

## 贡献指南

新增或修改技能前，请遵循[技能编写与维护规范](docs/skill-authoring.md)（英文）。规范涵盖精简且完整的内容、清晰排版、渐进披露、修改依据、通用性、安全问题判断及验证要求。

## 仓库结构

```text
agent-skills/
├── docs/
│   └── skill-authoring.md   # 技能编写与维护规范
├── skills/                  # Skill 目录
│   ├── drizzle-migration-conflict/ # Drizzle Kit 迁移冲突处理与预防
│   │   ├── SKILL.md         # Skill 入口文件
│   │   ├── references/      # 冲突处理、CI 策略、报告模板和来源链接
│   │   └── scripts/         # 只读迁移结构检查脚本
│   ├── git-stack/           # Git 提交、推送、冲突处理与工作树
│   │   ├── SKILL.md         # 技能入口文件
│   │   ├── commit.md        # 提交与推送流程
│   │   ├── conflict.md      # 合并与变基冲突处理
│   │   ├── validation.md    # 验证复用与失败分类
│   │   └── worktree.md      # 工作树创建与复用
│   ├── grill/               # 决策访谈与设计树
│   │   └── SKILL.md         # 技能入口文件
│   ├── hugo-to-markdown/    # Hugo 文档和内容转标准 Markdown
│   │   ├── SKILL.md         # Skill 入口文件
│   │   ├── agents/          # 智能体配置
│   │   ├── references/      # Hugo 转换规则
│   │   └── scripts/         # 规则盘点和校验脚本
│   ├── postgresql-cli/      # PostgreSQL 交互式终端 (psql)
│   │   ├── SKILL.md         # Skill 入口文件
│   │   └── references/      # 详细参考文件
│   ├── prd/                 # 产品需求生成
│   │   ├── SKILL.md         # 技能入口文件
│   │   └── reference/       # PRD 文档模板
│   ├── pre-release-review/  # 生产发布就绪度审查
│   │   ├── SKILL.md         # Skill 入口文件
│   │   └── references/      # 检查清单与报告模板
│   ├── rclone-cli/          # Rclone 云存储管理器
│   │   ├── SKILL.md         # Skill 入口文件
│   │   ├── references/      # 详细参考文件
│   │   └── scripts/         # 辅助脚本
│   ├── redis-cli/           # Redis 命令行界面
│   │   ├── SKILL.md         # Skill 入口文件
│   │   └── references/      # 详细参考文件
│   ├── to-spec/             # 根据 PRD 或明确指定的材料生成技术规格
│   │   ├── SKILL.md         # 中文技能入口文件
│   │   └── reference/       # SPEC 文档模板
│   └── to-task/             # 任务拆解与计划维护
│       ├── SKILL.md         # 技能入口文件
│       ├── references/      # 数据格式与对应的 JSON、Markdown 示例
│       └── scripts/         # 只读任务计划校验脚本
├── CLAUDE.md                # Claude Code 工作区指令
├── LICENSE                  # Apache 2.0 许可证
└── README.md                # 英文说明文件
```

## 许可证

[Apache License 2.0](LICENSE)

[drizzle-migration-conflict]: skills/drizzle-migration-conflict/SKILL.md
[git-stack]: skills/git-stack/SKILL.md
[grill]: skills/grill/SKILL.md
[hugo-to-markdown]: skills/hugo-to-markdown/SKILL.md
[postgresql-cli]: skills/postgresql-cli/SKILL.md
[prd]: skills/prd/SKILL.md
[pre-release-review]: skills/pre-release-review/SKILL.md
[rclone-cli]: skills/rclone-cli/SKILL.md
[redis-cli]: skills/redis-cli/SKILL.md
[to-spec]: skills/to-spec/SKILL.md
[to-task]: skills/to-task/SKILL.md
