# Agent-Skills

跨 Agent 的 `SKILL.md` 合集。格式跟 Claude / Codex / Grok / Kimi / Qwen 用的是同一套：每个 skill 一个目录，里面有 `SKILL.md`，可选 `scripts/`、`references/`。

本仓按领域分组存放；**安装时只把带 `SKILL.md` 的那一层拷到各 Agent 的 skills 目录**（扁平，名字全局唯一）。

## 安装

推荐用 [skills CLI](https://skills.sh/)（`npx skills`），和 [Ascend-Interface-Auditor](https://github.com/kali20gakki/Ascend-Interface-Auditor) 同一套。先确认仓能被识别：

```bash
npx skills add Sean1840/Agent-Skills --list
```

能列出 8 个 skill（`gitcode-review`、`gitcode-pr-summary`、`cann-prof-pipeline` 等）就可以装。

### 推荐：npx

```bash
# 全部 skill，装到本机已探测到的 Agent（用户级）
npx skills add Sean1840/Agent-Skills -g -y --all

# 指定 Agent（grok / claude-code / codex / cursor / opencode …）
npx skills add Sean1840/Agent-Skills -g -y -a grok
npx skills add Sean1840/Agent-Skills -g -y -a claude-code
npx skills add Sean1840/Agent-Skills -g -y -a codex

# 只装某一个
npx skills add Sean1840/Agent-Skills --skill gitcode-review -a grok -g -y
npx skills add Sean1840/Agent-Skills --skill cann-prof-pipeline -a claude-code -g -y

# 更新已安装的
npx skills check
npx skills update
```

`-g` 用户级；不加则装到当前项目（`.claude/skills/`、`.agents/skills/` 等）。多个 `--skill` 要分开写，不要逗号拼在一个参数里。

npx 拷贝每个 skill 自己的目录（`SKILL.md` + `scripts/` + `references/`）。cann 的共享文档和 `cann_analyze` 已放进 **`cann-prof-pipeline/references/` 与 `scripts/`**，装 pipeline 就会带上。其它 cann skill 通过 `../cann-prof-pipeline/references/...` 引用，所以 **cann 技能请一起装**（`--all` 或至少带上 `cann-prof-pipeline`）。Grok 也可以继续用 `~/.grok/config.toml` 的 `[skills].paths` 直接扫本仓。

### 本地配置（token / clone 路径）

机器相关项写在 `~/.agent-skills/config.json`，**第一次缺了必须问用户再写入**，不要猜盘符。GitCode token、检视 clone 根目录见 `gitcode-review/references/local-config.md`。

### 备选：仓内 install.py

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
cann/        Profiling / plog 分析（共享文档和工具在 cann-prof-pipeline 内）
wip/         草稿，不安装
install.py   跨 Agent 安装（备选）
package.json npm 元信息（npx skills 主要认 GitHub 上的 SKILL.md）
```

### cann（Profiling）

入口 skill：`cann-prof-pipeline`。共享文档在其 `references/`，`cann_analyze` 在其 `scripts/`。说明见 [cann/README.md](cann/README.md)。

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
