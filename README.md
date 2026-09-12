# Agent-Skills

自用 Grok skill 仓。每个 skill 是一个带 `SKILL.md` 的目录；Grok 递归扫描本仓。

## 挂到 Grok

`~/.grok/config.toml`：

```toml
[skills]
paths = ["E:/Code/Agent-Skills"]
ignore = ["E:/Code/Agent-Skills/wip"]
```

不要在 `~/.grok/skills/` 再留同名副本。

## 目录

```text
gitcode/     GitCode 检视、合入回顾
cann/        CANN 日志定位 / 收集 / 评测
msprof/      msprof 诊断
wip/         草稿（config ignore，不进自动触发）
```

每个 skill：

```text
<domain>/<name>/
  SKILL.md          必填，name 与文件夹名一致
  scripts/          会跑的脚本（可选）
  references/       长资料，需要时再读（可选）
```

## 加一个 skill

1. 已有领域就放进对应目录；没有就新建一层（不要再嵌套）。
2. 领域目录本身不要放 `SKILL.md`。
3. 全局 `name` 不能重复。
4. 半成品放 `wip/`。
