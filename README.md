# Agent-Skills

跨 Agent 的 `SKILL.md` 合集。格式跟 Claude / Codex / Grok / Kimi / Qwen 用的是同一套：每个 skill 一个目录，里面有 `SKILL.md`，可选 `scripts/`、`references/`。

本仓按领域分组存放；**安装时只把带 `SKILL.md` 的那一层拷到各 Agent 的 skills 目录**（扁平，名字全局唯一）。

## 安装

需要 Python 3.9+。在本仓根目录：

```bash
# 侦测本机已装的 Agent，装全部 skill（用户级）
python install.py

# 只装指定 Agent（可逗号分隔）
python install.py --agent grok,kimi,qwen,gpt

# 只装某个 skill
python install.py gitcode-review --agent grok

# 装进当前项目（团队共享，提交 .agents/skills 等）
python install.py --scope project

# 查看仓内 skill 和本机侦测结果
python install.py --list

# 卸掉
python install.py --uninstall --agent kimi
```

`--agent`：`grok` `gpt`/`codex` `kimi` `qwen` `deepseek` `claude` `cursor` `all`。

默认还会往 `~/.agents/skills/` 放一份（Codex / Kimi / 不少工具会扫这个通用目录）。不要这份就加 `--no-shared`。

Windows 优先建目录联接（改仓内文件即生效）；联接失败则复制。

### 各 Agent 落到哪

| Agent | 用户级 | 项目级 |
|---|---|---|
| Grok | `~/.grok/config.toml` 的 `[skills].paths` 指向本仓 | `.grok/skills/` |
| GPT / Codex | `~/.codex/skills/` | `.agents/skills/` |
| Kimi | `~/.kimi-code/skills/`（否则 `~/.agents/skills/`） | `.agents/skills/` |
| Qwen | `~/.qwen/skills/` | `.qwen/skills/` |
| DeepSeek | `~/.agents/skills/`（无独立 skills 目录时用通用路径） | `.agents/skills/` |
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| Cursor | `~/.cursor/skills/` | `.cursor/skills/` |

Grok 支持递归扫描本仓，所以用户级不扁平复制，避免和 `gitcode/gitcode-review` 重名。其它 Agent 只认「skills 根下的 `<name>/SKILL.md`」。

手动安装：把 `gitcode/gitcode-review/` **整个文件夹**放到上表对应目录，改名为 `gitcode-review`（已是这个名字则直接拷）。不要把 `gitcode/` 这一层拷进去。

## 目录

```text
gitcode/     GitCode 检视、合入回顾
cann/        Profiling / plog 分析（pipeline + parse + collect + 工具脚本）
wip/         草稿，不安装
install.py   跨 Agent 安装
```

### cann（Profiling）

入口 skill：`cann-prof-pipeline`。脚本在 `cann/tool/`（`python -m cann_analyze`）。说明见 [cann/README.md](cann/README.md)。

每个 skill：

```text
<domain>/<name>/
  SKILL.md
  scripts/        可选
  references/     可选
```

## 加一个 skill

1. 已有领域就放进对应目录；没有就新建一层（不要再嵌套）。
2. 领域目录本身不要放 `SKILL.md`。
3. 文件夹名 = `SKILL.md` 里的 `name`，全局不重复。
4. 半成品放 `wip/`。
5. `description` 写清做什么、何时触发；不要写死某一个 Agent 的产品名，除非流程真的只适用于它。
