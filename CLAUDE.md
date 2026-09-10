# CLAUDE.md

本文件是开发 agent-kit 仓库本身的工作指南。分发给宿主的核心规则在
`core/INSTRUCTIONS.md`(那是产品,不是本仓库的本地指令)。

## 项目定位

agent-kit 是代理无关的编码代理约束套件:1 份核心规则 + 8 个技能 + git 审计
提醒钩子,通过 `scripts/sync.py` 分发到 Claude Code(`~/.claude/`)、
Codex(`~/.codex/`)与 ZCode(`~/.zcode/`)。本仓库是规则的**源仓库**,
宿主目录只是分发目标。历史上(3b09b2a、8877bd7)专门清理过私有路径和
过程文档,内容必须保持通用、无私有信息。

## 架构:单一事实来源 → 渲染 → 分发

- `core/INSTRUCTIONS.md` — 核心规则唯一事实来源(英文)。
- `core/skills/<name>/` — 8 个技能源(`SKILL.md` + `references/` +
  `assets/` + 可选 `scripts/`),整目录分发。
- `adapters/{claude,codex,zcode}/` — 宿主入口文件,内含
  `<!-- AGENT-KIT:CORE:START/END -->` 渲染块及宿主专属说明。
- `scripts/sync.py` — 分发器。渲染在内存进行,**不反写 adapters**;
  adapters 里的渲染块用于生成与校验。

改核心规则的正确顺序:编辑 `core/INSTRUCTIONS.md` → 手工同步更新三个
adapter 入口文件中的渲染块及其 `.zh.md` 译本(参照 7925cea 的改法,
8 个文件一次提交)→ `python scripts/sync.py` 预览确认。绝不能只改
adapter 或只改 core 一侧。

## 常用命令

```bash
# 预览同步计划(默认零写入)
python scripts/sync.py

# 应用;--target 会显式创建缺失宿主目录
python scripts/sync.py --apply [--target {all,codex,claude,zcode}]

# 测试(纯标准库,无第三方依赖;sync.py test 内联跑同一套用例)
python scripts/sync.py test
python scripts/test_sync.py
python core/skills/sectioned-feature-development/scripts/test_section_plan.py
```

## 文件与编码约定

- 英文原版为准;每个英文文档同目录配中文译本,冲突以英文为准。
  译本不参与分发(`is_ignored_source` 排除 `*.zh.md`)。
- 译本命名有两种并存模式:`SKILL.md` → `SKILL.zh.md`,而 `references/`、
  `assets/` 下是 `xxx.md` → `xxx.md.zh.md`。新增译本跟随同目录既有模式。
- `.gitattributes` 对 `core/git-hooks/*`、`*.sh`、`*.py` 强制 LF;
  git hooks 依赖可执行位,勿破坏。
- `section_plan.py` 有两份必须保持一致的副本:顶层 `scripts/`(开发入口)
  与 `core/skills/sectioned-feature-development/scripts/`(随技能分发)。
  改动时两份同改。
- `adapters/codex/agents/*.toml`(三档 tier profile)不自动安装,
  由 Codex 用户手动复制,改模型名时记得同步说明。
- `.agent-work/` 已在 `.gitignore`(核心规则规定的计划工作区)。

## Git 约定

- Conventional Commits;常用 scope:`core` / `sync` / `skills` / `scripts` /
  `adapters` / `git-hooks` / `infra` / `docs` / `review`。
- `main` 是个人电脑版本;公司环境规则(SVN 边界、VS2008 路径、固定提交身份)
  保留在 `company` 分支,不要合并回 `main`。

## sync.py 安全语义(修改脚本时的硬约束)

`sync.py` 在 84de860(2026-09-10)被重写为安全优先,并配了 736 行测试。
改动脚本时必须保持以下保证,不得削弱:

- 默认只预览、零写入;`--apply` 重新计算计划,而非执行冻结快照。
- 所有目标全量预检:任一目标冲突 → 零目标写入。
- 文件按哈希保护;manifest(`<home>/.agent-kit/manifest.json`)记录状态;
  覆盖前备份到 `.agent-kit/backups/<batch-id>/`;逐文件原子替换;失败回滚。
- 覆盖已确认冲突的文件必须走按文件授权的 `--replace TARGET:REL_PATH`,
  且不绕过路径安全、manifest 校验与备份。
- 绝不修改宿主的 `cli/config.json`、`settings.json`、plugins 等运行配置。
- 改动 sync.py 后必须跑 `python scripts/sync.py test` 全绿再提交。
