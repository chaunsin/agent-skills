# worktree

确保在隔离的工作空间中进行工作。优先使用平台自带的工作树工具。仅当没有自带工具可用时才考虑手动创建 Git 工作树。

**核心原则：** 首先检测已存在的隔离机制。然后使用原生工具。如果存在隔离机制，则回退到 Git。切勿与底层机制对抗。
**开始时声明：** “我正在使用 git-stack 技能来设置一个隔离的工作区。”

## 何时创建工作树

**仅当您尚未**隔离且需要一个单独的工作空间时才创建

- 明确指定创建操作。
- 并行运行多个功能而无需分支切换开销
- 审核 PR 的同时，保持当前签出状态空闲，以便进行其他工作。

## 步骤1: 检测现有隔离

**创建任何内容之前，请检查您是否已在隔离的工作区中。**

```shell
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
```

**子模块守则：** `GIT_DIR != GIT_COMMON`在 Git 子模块内部也适用。在得出“已在工作树中”的结论之前，请确认您不在子模块中：

```shell
# If this returns a path, you're in a submodule, not a worktree — treat as normal repo
git rev-parse --show-superproject-working-tree 2>/dev/null
```

**如果`GIT_DIR != GIT_COMMON`（且不是子模块）：** 您已位于已链接的工作树中。请跳至步骤 2（项目设置）。请勿创建另一个工作树。

报告分支状态：

- 在分支上：“已经在`<path>`分支上的隔离工作区中`<name>`。”
- 分离的 HEAD：“已位于隔离的工作区`<path>`（分离的 HEAD，外部管理）。需要在完成时创建分支。”

**如果`GIT_DIR == GIT_COMMON`（或在子模块中）：** 您正在进行正常的仓库检出。

用户是否已在您的说明中表明其工作树偏好？如果没有，请在创建工作树之前征得用户同意：

> “你想让我创建一个隔离的工作树吗？它可以保护你当前的分支免受更改。”

尊重用户已声明的任何偏好，无需询问。如果用户拒绝同意，则按原计划进行操作，并跳至步骤 2。

## 步骤2: 创建独立工作区

**你有两种方法。请按此顺序尝试。**

### 2a. 原生 Worktree 工具（首选）

用户已请求一个独立的工作区（步骤 0：同意）。您是否已有创建工作树的方法？它可以是一个工具（例如 `<worktree_name>`）`EnterWorktree`、`WorktreeCreate`一个`/worktree`命令或一个`--worktree`标志。如果有，请使用它并跳至步骤 2。

原生工具会自动处理目录放置、分支创建和清理工作。`git worktree add`如果使用原生工具，则会创建你的框架无法识别或管理的“幽灵状态”。

只有在没有可用的原生工作树工具的情况下，才继续执行步骤 1b。

### 2b. Git 工作树回退

**仅当步骤 2a 不适用时才使用此方法**——即您没有可用的原生工作树工具。使用 Git 手动创建工作树。

#### 目录选择

请遵循以下优先级顺序。用户明确偏好始终优先于观察到的文件系统状态。

1. **检查您的用户手册中是否已声明工作树目录首选项。** 如果用户已指定，则无需询问即可使用。
2. **检查是否存在项目本地工作树目录：** 如果找到就用它。如果两者都存在，则`.worktrees`胜出。

    ```shell
    ls -d .worktrees 2>/dev/null     # Preferred (hidden)
    ls -d worktrees 2>/dev/null      # Alternative
    ``` 
3. **如果没有其他指导**，则默认`.worktrees/`位于项目根目录。

#### 安全验证（仅限项目本地目录）

**创建工作树之前，必须确认目录已被忽略：**

```shell
git check-ignore -q .worktrees 2>/dev/null || git check-ignore -q worktrees 2>/dev/null
```

**如果未被忽略：** 添加到 .gitignore 文件中，提交更改，然后继续。
**关键性：** 防止意外地将工作树内容提交到存储库。

#### 创建工作树

```shell
# Determine path based on chosen location
path="$LOCATION/$BRANCH_NAME"

git worktree add "$path" -b "$BRANCH_NAME"
cd "$path"
```

**沙箱回退方案：** 如果`git worktree add`因权限错误（沙箱访问被拒绝）而失败，则告知用户沙箱阻止了工作树的创建，并且当前目录正在运行。然后，在当前目录下运行设置测试和基线测试。

## 步骤3: 检测新工作区

运行测试以确保工作区启动时状态良好：

```shell
# Use project-appropriate command
npm test / cargo test / pytest / go test ./...
```

**如果测试失败：** 报告失败情况，询问是继续进行还是进行调查。
**如果测试通过：** 报告已准备就绪。
**报告:**

```text
Worktree ready at <full-path>
Tests passing (<N> tests, 0 failures)
Ready to implement <feature-name>
```

## 边缘回退

| 问题与情况 | 方案 |
| ------------------------------------- | ------------------------------------- |
| 已在链接的工作树中 | 跳过创建（步骤 0） |
| 在子模块中 | 按照普通仓库处理（步骤 0 保护） |
| 原生工作树工具可用 | 使用它（步骤 1a） |
| 没有原生工具 | Git 工作树回退（步骤 1b） |
| `.worktrees/`或 `worktrees/` 存在 | 使用它（验证是否忽略） |
| 存在 | 使用它（验证是否忽略） |
| 两者都存在 | 使用`.worktrees/` |
| 两者都不存在 | 检查指令文件，然后默认`.worktrees/` |
| 目录未被忽略 | 添加到 .gitignore 文件 + 提交 |
| 创建时出现权限错误 | 沙盒备选方案，就地工作 |
| 基线测试失败 | 报告故障 + 询问 |
| 没有 package.json/Cargo.toml 文件 | 跳过依赖安装 |
| `git worktree add`当平台已经提供隔离功能时仍需使用此功能 | 步骤 0 检测已存在的隔离状态。步骤 1a 则交由原生工具处理。 |
| 在现有工作树内创建嵌套工作树 | 在创建任何内容之前，务必先运行步骤 0。 |
| 工作树内容被跟踪，污染了 Git 状态。 | 始终`git check-ignore`在创建项目本地工作树之前执行此操作 |
| 造成不一致，违反项目规范 | 造成不一致，违反项目规范 |
| 无法区分新出现的错误和原有问题 | 报告失败，并获得明确许可才能继续操作。 |
