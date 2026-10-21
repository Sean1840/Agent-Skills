# Agent-Skills

给编码 Agent 用的工作流技能：GitCode 开 PR 行内检视、已合入 PR 的合入回顾，以及全库冗余清理。每个 skill 一个目录，内含 `SKILL.md`，可选 `scripts/`、`references/`。

安装时只把带 `SKILL.md` 的那一层拷到各 Agent 的 skills 目录（扁平，名字全局唯一）。

## Skills

| Skill | 做什么 | 何时用 |
|---|---|---|
| `gitcode-review` | 把 GitCode PR 的 patch 落到本地仓，对照周边代码和调用链检视，把意见钉到 Files 页具体行 | 「检视这个 PR」「给 GitCode 提行内意见」`/gitcode-review` |
| `gitcode-pr-summary` | 按合入时间窗口总结已进 master 的改动：diff 实际改了什么、做法、风险、相关 PR | 「总结近一周合入」「master 这周改了什么」`/gitcode-pr-summary` |
| `codebase-slop-audit` | 分块通读调用链，查找无用测试、多余包装、死代码和重复抽象，编排者亲自复核后给排序计划 | 「全库清理」「无用测试」「冗余抽象」`/codebase-slop-audit` |

前两个只对 GitCode。GitHub / GitLab PR 不要走这两条。`codebase-slop-audit` 不绑托管平台。

### gitcode-review

1. 拉 PR 元数据和改动文件清单。
2. 在**检视专用 clone** 上 checkout head，对照全仓读实现，不要只盯 diff。
3. 意见必须落到 HEAD 新文件行号；格式：`[review]【维度】标题` + 问题 / 修复 / 示例。
4. 发帖用 `scripts/post_inline_comment.py`（`path` + `position` + `commit_id`）。没有 token 时只在对话里列出「文件 + 行号 + 正文」。

缺 GitCode token 或 clone 路径时先问用户，写入本地配置后再继续。不要猜盘符。细则见 [gitcode-review/references/local-config.md](gitcode/gitcode-review/references/local-config.md)。

### gitcode-pr-summary

1. 列出窗口内合入基准分支的 PR（默认近 7 天、`Ascend/msprof`、`master`；用户点名仓/时间/路径前缀则按用户的）。
2. 每笔 PR 对照描述和 diff，以代码为准；描述没提的夹带要写出来。
3. 只有「同文件且方法相关」才能合成一条修改点。
4. 输出一篇 markdown，不要往业务仓提交，也不要用行内评论接口发这些结论。

clone 路径、回顾 md 输出目录同样走本地配置。没有则先问。

### codebase-slop-audit

1. 父会话只编排。蜂群是新会话，模型和正在执行本 skill 的会话相同，推理强度用该模型的最高档。
2. 先把仓库分成能通读的小块。每块先查找，再换一个新会话做对抗复查。查找和复查只列目录、通读文件，不靠内容搜索或符号索引下结论。
3. 编排者自己读幸存目标，给出排序后的清理计划。没有发现也算做完。这一步不改仓库。
4. 用户要求清理时，新会话按计划修改，另一个新会话重读并跑相关测试。剩下的问题由父会话自己收。

细则见 [codebase-slop-audit/SKILL.md](audit/codebase-slop-audit/SKILL.md)。

## 安装

```bash
npx skills add Sean1840/Agent-Skills --list
npx skills add Sean1840/Agent-Skills -g -y --all
npx skills add Sean1840/Agent-Skills --skill gitcode-review -a grok -g -y
npx skills add Sean1840/Agent-Skills --skill codebase-slop-audit -a grok -g -y
npx skills check
npx skills update
```

`-g` 用户级；不加则装到当前项目。多个 `--skill` 要分开写。npx 拷贝每个 skill 自己的目录（`SKILL.md` + `scripts/` + `references/`）。

备选：仓根 `python install.py`（Python 3.9+）。`--list` 看仓内 skill；`--agent grok,kimi` 指定 Agent；`--scope project` 装进当前项目。

| Agent | 用户级 | 项目级 |
|---|---|---|
| Grok | `~/.grok/config.toml` 的 `[skills].paths` 指向本仓 | `.grok/skills/` |
| GPT / Codex | `~/.codex/skills/` | `.agents/skills/` |
| Kimi | `~/.kimi-code/skills/` | `.agents/skills/` |
| Qwen | `~/.qwen/skills/` | `.qwen/skills/` |
| DeepSeek | `~/.agents/skills/` | `.agents/skills/` |
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| Cursor | `~/.cursor/skills/` | `.cursor/skills/` |

Grok 可递归扫本仓，用户级不必再扁平复制。其它 Agent 只认 skills 根下的 `<name>/SKILL.md`，拷贝时不要带上 `gitcode/` 这一层。

## 本地配置

机器相关项写在 `~/.agent-skills/config.json`（可用 `AGENT_SKILLS_CONFIG` 改路径）。**第一次缺了必须问用户再写入**，不要猜盘符。

```bash
python gitcode/gitcode-review/scripts/local_config.py show
python gitcode/gitcode-review/scripts/local_config.py set gitcode.review_root ~/review
python gitcode/gitcode-review/scripts/local_config.py set-clone Ascend/msprof ~/review/msprof
```

| 项 | 配置 | 建议默认（只展示，须确认） |
|---|---|---|
| GitCode token | 环境变量 `GITCODE_API_TOKEN`，或 `gitcode.api_token` | 无，用户从 GitCode 个人设置 → 访问令牌获取 |
| 检视 clone 根目录 | `gitcode.review_root` | `~/review` |
| 某仓 clone | `gitcode.clones["owner/repo"]` | `{root}/{repo}` |
| 合入回顾输出目录 | `gitcode.summary_output_dir` | `{root}` |

Token 不要回显、不要提交进 git。

## 目录

```text
gitcode/gitcode-review/              开 PR 行内检视
gitcode/gitcode-pr-summary/          已合入 PR 回顾
audit/codebase-slop-audit/           全库冗余清理
wip/                                 草稿，不安装
install.py                           跨 Agent 安装
```

每个 skill：

```text
<name>/
  SKILL.md
  scripts/        可选
  references/     可选
```

加 skill：文件夹名 = `SKILL.md` 的 `name`；领域目录本身不要放 `SKILL.md`；半成品放 `wip/`。
