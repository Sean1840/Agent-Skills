# 本地配置（首次必问）

机器相关的 token、clone 路径、输出目录，**第一次缺了就停下来问用户**，确认后再写入本地配置。禁止自行选用 `E:\Code\review` 或其它盘符/目录。

配置文件：`~/.agent-skills/config.json`（环境变量 `AGENT_SKILLS_CONFIG` 可改路径）。

```bash
python <this-skill>/scripts/local_config.py show
python <this-skill>/scripts/local_config.py set gitcode.review_root ~/review
python <this-skill>/scripts/local_config.py set-clone Ascend/msprof ~/review/msprof
python <this-skill>/scripts/local_config.py set-cann-repo ascend/msprof /path/to/msprof
```

## 何时问、问什么

| 项 | 配置 | 建议默认（只展示，须确认） | 没有时 |
|---|---|---|---|
| GitCode token | 环境变量 `GITCODE_API_TOKEN`，或 `gitcode.api_token` | 无 | 说明去 GitCode 头像 → 个人设置 → 访问令牌；用户给出后 `set_token`，不要回显 |
| 检视 clone 根目录 | `gitcode.review_root` | `~/review` | 问「PR 代码放到哪」；可建议 `~/review`，用户点头再写 |
| 某仓 clone | `gitcode.clones["owner/repo"]` | `{review_root}/{repo}` | 根目录已确认则可推导；用户指定绝对路径则按指定写 |
| 合入回顾 md | `gitcode.summary_output_dir` | `{review_root}` | 同根目录；不要写进业务仓 |

已有配置则直接用，不再问。用户说改路径/token 时覆盖写入。

Token 优先读环境变量，其次读配置文件。写入时同时写配置文件；Windows 上再写用户环境变量。不要把 token 提交进任何 git 仓。

## Agent 动作

1. `local_config.py show`（或 load）。
2. 缺 `clone_path` / token（仅发帖需要）→ 用用户的话确认，禁止先 clone 到未确认路径。
3. 确认后 `set` / `set-clone` / `set_token`，再 `git clone` / fetch。
4. 开发仓（用户日常改代码的那份）与检视 clone **分开**；检视 clone 可以随意 checkout。开发仓路径也要用户指认，不要猜。
