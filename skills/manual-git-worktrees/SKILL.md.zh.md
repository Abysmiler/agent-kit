<!-- 中文翻译版；英文原版为本目录同名 .md 文件。若两者不一致，以英文版为准。 -->

---
name: manual-git-worktrees
description: Use only when the user explicitly asks to create or use an isolated git worktree. Coordinate active-agent scope files under `.worktrees/current-agents/`, set up a `.worktrees/` workspace, verify existing isolation first, ensure `.worktrees/` is ignored before creation, and report whether the ignore rule was committed. Do not use automatically for ordinary implementation, debugging, or planning.
---

# 手动 Git Worktree（Manual Git Worktrees）

仅在显式调用时使用本技能。

## 工作流

1. 先检测既有隔离。
   - 运行 `git rev-parse --show-toplevel`、`git rev-parse --git-dir`、`git rev-parse --git-common-dir`、`git rev-parse --show-superproject-working-tree` 和 `git branch --show-current`。
   - 如果已处于一个链接式 worktree 中，报告当前路径与分支并停止。
   - 如果位于 submodule 内，将其视作普通检出（checkout）。

2. 在写入任何新的范围文件之前，先检查活动代理范围冲突。
   - 以仓库根目录下的 `.worktrees/current-agents/` 作为活动代理注册表。
   - 在创建或修改任何注册表文件之前，阅读 `.worktrees/current-agents/` 下所有既有的 `*.md` 文件。
   - 如果 `.worktrees/current-agents/` 不存在，视作注册表中没有活动条目。
   - 注册前先估计当前任务范围：预期目标、可能涉及的模块/组件/工作流，以及可能被修改的文件或路径模式。
   - 将估计的范围与每条既有注册表条目比较。
   - 将以下情形视为冲突：文件重叠、路径模式重叠、共享所有权边界、迁移/schema 变更、共享状态、路由、构建/配置文件，或所有权不明确。
   - 如果在开始前发现冲突，立即停止。告知用户哪个注册表文件/任务冲突、哪些范围重叠，并建议在该冲突任务完成后再开始本任务。
   - 如果之后因任务范围变化而出现冲突，立即停止并给出同样的冲突报告。
   - 只忽略两个代理在任何一方写入前同时读取注册表的极端竞态。

3. 选择 worktree 位置。
   - 使用仓库根目录下的 `.worktrees/`。
   - 每个任务一个分支，使用简短的、任务专属的分支名。

4. 在 `.worktrees/` 下创建任何内容之前，先确保 `.worktrees/` 已被忽略。
   - 检查 `.gitignore` 是否已忽略 `.worktrees/`。
   - 若没有，先将 `.worktrees/` 加入 `.gitignore`。
   - 如果仓库没有其他脏路径，暂存并提交这一条忽略改动。
   - 如果仓库已有其他被修改的文件，保持 `.gitignore` 改动未提交并报告它。
   - 在你正在使用的仓库检出中存在该忽略规则之前，不要创建 worktree。

5. 冲突检查通过后注册本任务。
   - 需要时创建 `.worktrees/current-agents/`。
   - 以任务目标命名创建一个 Markdown 文件，例如 `.worktrees/current-agents/fix-login-timeout.md`。
   - 如果自然文件名已存在，添加一个简短的唯一后缀，而不是覆盖它。
   - 记录足够详细的信息，以便其他代理检测冲突：
     - 任务目标。
     - 预期范围与非目标。
     - 可能被修改的文件、目录、模块、路由、schema、配置文件或工作流。
     - 当前分支与计划的 worktree 路径。
     - 开始时间。
   - 如果任务目标或实现范围发生实质性变化，先更新此文件再继续工作。

6. 创建 worktree。
   - 优先使用环境提供的任何原生 worktree 辅助工具。
   - 否则在 `.worktrees/` 下使用 `git worktree add`。

7. 验证新工作区。
   - 仅按需运行仓库的正常设置或基线检查，以确认隔离工作区可用。
   - 如果基线本已失败，先报告该情况再继续功能工作。

8. 报告结果。
   - 包含完整的 worktree 路径、分支名、忽略规则状态与基线状态。
   - 除非用户在同一请求中要求，否则不要切换进实现模式。

9. 收尾时清理活动代理注册表条目。
   - 只删除为本任务创建的注册表 Markdown 文件。
   - 在任务完成、放弃或受阻时、将控制权交还用户之前执行此操作。
   - 如果需要等待另一个活动代理，报告冲突并结束回复，而不是保持任务挂起。

## 与 sectioned-feature-development 的关系

本技能拥有 agent-kit 中唯一的 worktree 约定。sectioned-feature-development
工作流在同一 `.worktrees/` 工作区下创建其重试与并行章节（section）的
worktree，并使用本技能的冲突检查协议将每个活动任务注册到
`.worktrees/current-agents/`。当两者同时活跃时，注册表是范围冲突的
唯一事实来源。
