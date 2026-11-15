# CLAUDE.md

本文件是开发 agent-kit 仓库本身的工作指南。分发给宿主的规则在 `rules/core.md`
(那是产品,不是本仓库的本地指令)。

## 项目定位

agent-kit 是个人使用、可公开的编码代理约束套件:一份常驻规则 + 6 个技能,
通过 `bin/sync.mjs` 分发到 Claude Code(`~/.claude/`)、Codex(`~/.codex/`)
与 ZCode(`~/.zcode/`)。本仓库是**源仓库**,宿主目录只是分发目标。
仓库内容必须通用、无私有信息;私有内容只放 `local/`(被 git 忽略)。

设计取向:日常路径尽量轻,规则尽量短。新增规则前先问"每次会话都需要它吗",
不是就放进技能;新增流程文件、评审轮次或模板前先问能否不加。

## 架构:一处编辑 → 同步时拼装 → 分发

- `rules/core.md` — 常驻规则唯一事实来源(英文)。保持在 60 行以内。
- `hosts/host-<宿主>.md` — 该宿主专属的几行(项目规则位置、档位映射)。
  文件名不能叫 `claude.md`:在不区分大小写的文件系统上会被当成 `CLAUDE.md` 加载。
- `skills/<name>/` — 技能源,整目录分发。单文件优先,最多一个 `references/` 文件。
- `local/` — 本机覆盖层(`rules.md`、`skills/`),不进仓库。
- `bin/sync.mjs` — 分发器。受管块 = core + host + local/rules.md,在内存中拼装,
  仓库里不保存渲染结果。

改规则只改 `rules/core.md`(及其 `core.zh.md`),然后 `node bin/sync.mjs` 预览。

## 常用命令

```bash
node bin/sync.mjs                 # 预览(零写入)
node bin/sync.mjs --apply [--target {auto,all,claude,codex,zcode}]
node --test bin/                  # 测试(零依赖)
```

## 文件约定

- 英文原版为准。只有 `rules/core.md` 和各 `SKILL.md` 配中文译本,命名统一为
  `core.zh.md` / `SKILL.zh.md`;改英文时同步改译本。译本不分发。
- 技能正文与宿主无关:不出现具体宿主或模型名,子代理用 `[tier: execute]` /
  `[tier: review]`。宿主差异只写在 `hosts/` 和 `init-project` 的参考文件里。
- `.gitattributes` 对钩子、`*.sh`、`*.mjs` 强制 LF。
- `hosts/codex-agents/*.toml` 不自动安装,改模型名时同步 README 说明。

## Git 约定

- Conventional Commits;常用 scope:`rules` / `skills` / `sync` / `hosts` / `docs`。
- 公司环境规则不进仓库,放在公司机器的 `local/rules.md`。

## sync.mjs 安全语义(修改脚本时的硬约束)

改动脚本时必须保持以下保证,并且 `node --test bin/` 全绿后再提交:

- 默认只预览、零写入;`--apply` 重新计算计划。
- 所有目标全量预检:任一目标冲突 → 零目标写入。
- 文件按哈希保护;manifest(`<home>/.agent-kit/manifest.json`)记录基线;
  覆盖或删除前备份到 `.agent-kit/backups/<批次>/`;逐文件原子替换。
- 只删除本工具安装过且未被改动的文件;manifest 里的路径必须通过安全校验。
- 覆盖冲突文件必须走按文件授权的 `--replace HOST:REL_PATH`。
- 入口文件只动受管块;无标记时追加,不替换原内容。
- 不穿过符号链接/junction 写入;绝不修改宿主的运行配置。
