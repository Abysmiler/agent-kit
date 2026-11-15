# agent-kit

代理无关的编码代理约束套件:一份简短的常驻规则 + 6 个技能,分发到
**Claude Code**、**Codex** 与 **ZCode**。只依赖 Node(三个宿主本身都需要它)。

## 快速开始

```bash
node bin/sync.mjs                    # 预览:只打印计划,不写任何文件
node bin/sync.mjs --apply            # 写入所有已存在的宿主目录
node bin/sync.mjs --apply --target zcode   # 只写某个宿主;目录不存在时会创建
node --test bin/                     # 运行同步工具的测试
```

同步后各宿主得到:

| 宿主 | 入口文件 | 技能目录 |
|---|---|---|
| Claude Code | `~/.claude/CLAUDE.md` | `~/.claude/skills/` |
| Codex | `~/.codex/AGENTS.md` | `~/.codex/skills/` |
| ZCode | `~/.zcode/AGENTS.md` | `~/.zcode/skills/` |

## 工作流

规则按"日常路径尽量轻,重流程只留给真正需要的场景"来组织:

| 场景 | 做法 |
|---|---|
| 普通改动(绝大多数) | 实现 → 验证 → 汇报。不分节,不走评审循环 |
| 需求不清 | 显式调用 `grill-me`,只问该由人决定的产品语义 |
| 要评审 | `code-review`:一次独立评审;修复后由主代理自验,不自动加轮次 |
| 改动既大又跨高风险边界,或整体实现未收敛 | `sectioned-feature-development`:一个计划文件 + 一个状态文件,逐节实现、每节评审一次 |
| 修了一次没修好 / 调试变长 | `systematic-debugging`:证据 → 单一假设 → 最小修复;可选沉淀为工程笔记 |
| 定期体检 | `code-audit`:单个持久文件记录覆盖与发现,跨周期深化 |
| 新仓库接入 | `init-project`:生成项目级规则,可选安装 git 审计提醒钩子 |
| 需要隔离工作区 | 显式调用 `manual-git-worktrees` |

## 目录结构

```
agent-kit/
├── rules/core.md          # 常驻规则,唯一事实来源(core.zh.md 为译本)
├── hosts/host-<宿主>.md   # 每个宿主自己的几行说明(路径、档位映射)
├── hosts/codex-agents/    # Codex 档位 profile,需手动复制到 ~/.codex/agents/
├── skills/<name>/         # 技能(SKILL.md 为准,SKILL.zh.md 为译本)
├── local/                 # 本机覆盖层,不进仓库,见 local/README.md
└── bin/sync.mjs           # 分发工具及其测试
```

改规则只需改一处:编辑 `rules/core.md` 或技能文件,然后同步。宿主入口里的
受管块由 `rules/core.md` + `hosts/host-<宿主>.md` + `local/rules.md`(可选)
在同步时拼出,仓库里不保存渲染结果。

`*.zh.md` 译本只供人阅读,不分发;只有 `rules/core.md` 和各 `SKILL.md` 配译本,
与英文不一致时以英文为准。

## 同步语义

- **默认只预览。** 只有 `--apply` 才写入,并且写入前重新计算计划。
- **任一宿主有冲突,所有宿主都不写。**
- **入口文件**只管理 `<!-- AGENT-KIT:CORE:START/END -->` 之间的块:
  - 文件不存在 → 新建;
  - 存在但没有标记 → 保留原内容,在末尾追加受管块;
  - 有标记 → 只替换块内文本,块外内容原样保留;
  - 块内被手工改过,或标记损坏 → 冲突。
- **技能文件**按哈希保护:
  - 你改过、源没变 → 保留你的版本;
  - 双方都改,或同名文件不是本工具装的且内容不同 → 冲突;
  - 源里删掉的文件:你没动过 → 删除;你改过 → 保留并提示;
  - 不是本工具装的文件和技能永远不碰。
- **覆盖或删除前先备份**到 `<宿主目录>/.agent-kit/backups/<批次>/`;
  状态记录在 `<宿主目录>/.agent-kit/manifest.json`。
- **冲突由你逐个文件授权:** `--replace 宿主:相对路径`,可重复,例如
  `node bin/sync.mjs --apply --replace codex:skills/code-review/SKILL.md`。
- 拒绝穿过符号链接或 junction 写入;从不修改宿主的 `settings.json`、
  `config.toml`、`cli/config.json`、插件等运行配置。
- 写入是逐文件原子替换,但不是跨文件事务:中途失败时已写入的文件与源一致,
  下次运行会自动接管,被替换的旧文件在备份目录里。

## 本机覆盖层

公司规则、私有路径、私有技能放在 `local/`(被 git 忽略):`local/rules.md`
追加到受管块末尾,`local/skills/<name>/` 随技能一起分发。只针对单个宿主的
个人偏好直接写在宿主入口文件的受管块之外即可。

## 模型档位

技能用两个角色档位路由子代理,映射写在各 `hosts/host-<宿主>.md` 里:

| 档位 | 用途 |
|---|---|
| `[tier: execute]` | 常规实现 |
| `[tier: review]` | 评审、修复、高风险实现;总是全新上下文 |

Codex 的 profile 在 `hosts/codex-agents/*.toml`,不自动安装:
`cp hosts/codex-agents/*.toml ~/.codex/agents/`,按需替换其中的模型名。

## Git 审计提醒钩子

非阻塞的提交计数提醒,随 `init-project` 技能分发(`assets/githooks/`),
由该技能引导安装到目标仓库的 `.githooks/`。

```bash
git config --local agentkit.maintainabilityAuditInterval 50   # 每 50 次提交提醒一次
git config --local agentkit.maintainabilityAuditBaseline <sha> # 可选基线
```

审计完成后的提交带 `Maintenance-Audit: true` trailer 即重置计数;提示只输出到
stderr 且永远 exit 0;`AGENTKIT_MAINTAINABILITY_AUDIT_REMINDER=0` 可临时静默。
