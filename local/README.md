# local/ — 本机覆盖层(不进仓库)

这个目录里除了本文件和 `.gitignore`,其余内容都被 git 忽略。放只属于这台机器
或这个环境的东西:公司规则、私有路径、私有技能。

| 路径 | 作用 |
|---|---|
| `local/rules.md` | 追加到每个宿主的受管规则块末尾(在核心规则和宿主说明之后) |
| `local/skills/<name>/` | 与 `skills/` 一起分发的私有技能;名字不能与 `skills/` 里的重复 |

改完后照常运行 `node bin/sync.mjs` 预览,再 `--apply`。

只针对某一个宿主的个人偏好不必放这里:直接写在宿主入口文件
(`~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md`、`~/.zcode/AGENTS.md`)的受管块
**之外**即可,同步永远不会动块外的内容。
