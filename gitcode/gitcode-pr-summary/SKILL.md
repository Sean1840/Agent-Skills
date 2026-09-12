---
name: gitcode-pr-summary
description: >
  Collect merged PRs on a GitCode repo in a time window, analyze the landed
  code against the whole tree, and write a markdown retrospective: what the
  diff actually changed (not the PR description), how, risks, related PRs,
  and which branch each PR merged into. Use when the user asks about a
  GitCode repo with 合入回顾、总结xx仓、总结近一周的pr合入、近一周的PR合入、
  master 一周改了什么、一周合入了什么、业务代码审视、回顾已合入 PR, or runs
  /gitcode-pr-summary. GitCode only. Not for GitHub/GitLab. Not for commenting
  on an open PR (use gitcode-review).
---

# GitCode master 合入回顾

对**已经合入 master** 的业务改动做整仓分析与总结，输出一份 markdown。目标是让人看懂这段时间合了什么、怎么做的、有没有坑、和前后 PR 的关系。合入分支只写 PR 实际进了哪些；对照分支（商发等）只在用户点名时才算时差。

不要做成开 PR 行内检视（那是 `gitcode-review`）。GitHub / GitLab 仓不要走本 skill。

## 输入（缺省就用默认，不要反复问仓链接）

| 项 | 默认 | 说明 |
|---|---|---|
| 仓 | `Ascend/msprof` | GitCode `owner/repo`。本地只在 `E:\Code\review\msprof` 拉代码，不要动 `E:\Code\msprof` |
| 基准分支 | `master` | 合入统计以该分支为准 |
| 时间范围 | **最近 7 天** | 按 **合入 master 的时间**（`merged_at`），不是创建 PR 的时间。用户说近 N 天/周/月就按那个窗口 |
| PR 范围 | **全部合入** | 可收窄：作者、标题关键词、**路径前缀**（如只要 `profiler/`、`src/profiler/`） |
| 对照分支 | 无 | 仅当用户点名（如某商发 / release）才 fetch 并算「master 合入后过了几天」。未点名不要自行寻找版本分支 |

用户说「回顾上周 msprof」或「总结 xx 仓，近一周的 pr 合入」这类话时：仓从话里取（未说则 msprof）、一周、全部 PR，直接开跑。指定了路径前缀时只分析 diff 命中这些路径的 PR；同 PR 改了范围外文件，在「描述 vs 代码」里一句带过，不展开。非 msprof 仓落到 `E:\Code\review\{repo}`，不要动用户开发仓。

认证：`GITCODE_API_TOKEN`。没有 token 时用 git log 凑合列 commit，并写明「PR 元数据不全」。

## 工作流

1. `cd E:\Code\review\msprof && git fetch origin master`。用户点名了对照分支才再 fetch 那些分支。检出 `origin/master`。目录不是 git 仓则先 `git clone git@gitcode.com:Ascend/msprof.git E:\Code\review\msprof`。
2. 列出窗口内合入 master 的 PR（脚本优先，见下）。用户指定了路径前缀时：用 `git log origin/master --since -- <paths>` 和/或 files API，**只保留 diff 命中这些前缀的 PR**；未改这些路径的合入不进修改点。过滤 docs-only / 纯 CI 可在文档里单列「非业务」，不要混进业务修改点。
3. **描述检查 → 代码核对**（每笔 PR 必须两步都做，以代码为准）：
   1. 读标题和描述，记下它**声称**改了什么。
   2. `git show <merge_sha>` 或 `git diff <base>...<merge>`，再读合入后的整文件与调用链（作用、调用方、数据流、失败路径）。列出实际改了哪些文件、函数、行为。
   3. 「做了什么」只根据第 2 步写。描述与 diff 不符、描述没提但 diff 里有的改动（夹带），写进「描述 vs 代码」，不能当没发生。禁止只根据 PR 描述当作修改内容。
4. **归并修改点**：只有「相关代码」才能合成一条或写入「关联」。**相关代码**两条同时满足：
   - 存在相同的修改文件（两笔 diff 的 path 有交集）；
   - 且这些交集文件上，改动的方法/逻辑有相关性（同一函数、同一条数据流、或修同一缺陷的前后迭代）。
   只共享文件但改的是不相干函数，或主题像、同日合入、同一作者、同属一波 C 化但文件无交集，都单列。修复型 PR 沿同一文件+同一方法往前追引入点；引入 PR 的编号和合入日期写在**本条修改点里**（窗外也一样），不要另开「窗口外根因」附录。
5. **合入分支**：只写该 PR 的 `base`（实际合入了哪些）。用户点名对照分支时，再对代表 commit 做 `git merge-base --is-ancestor`，用对照分支上**首次包含该 sha 的提交日期**写时差。未点名则停，不要 `git branch -r --contains` 去扫 `26.*`、`release*`、`shop*` 等。
6. 写成一篇 md，交给用户。默认路径：`E:\Code\review\msprof-合入回顾-<from>_to_<to>.md`。不要往业务仓里提交这篇文档。

## 拉 PR 列表

优先 API（需 token）：

```
python <this-skill>/scripts/list_merged_prs.py --owner Ascend --repo msprof --base master --days 7
```

脚本打 JSON：number、title、html_url、merged_at、user、base、merge_commit_sha。再用

```
GET /api/v5/repos/{owner}/{repo}/pulls/{n}
GET /api/v5/repos/{owner}/{repo}/pulls/{n}/files?per_page=100
```

拿正文和文件清单。`patch` 可能是对象，只当范围，分析必须 `git show` 整文件。

无 token 时：

```
git log origin/master --since='7 days ago' --pretty=format:'%H %cI %s'
```

能列 commit，对不上 PR 号就在文档里标明。

## 每个修改点必须写清

- **做了什么**：只写代码里实际发生的事。描述只作对照，不作事实来源。
- **描述 vs 代码**：声称的改动 vs diff；漏写、写反、夹带（描述没有、diff 里有）都点名文件/函数。
- **怎么完成的**：关键路径（入口 → 解析/计算/导出或测试编排），点名文件，不要贴整份 diff。
- **风险 / 遗漏**：开关未开、失败静默、脏数据、UT 只覆盖快乐路径、同类模块已有实现却另起一套。要有依据（对照了哪处现有代码）。没有把握就写「未核对」。
- **引入**：这笔代码修的是何时引入的问题。写引入 PR/提交的编号、链接和合入日期，与本条修复放在一起。找不到就写「未核对引入点」，不要把根因拆到文末。
- **关联**：仅「相关代码」（同文件且方法/逻辑相关）的后续修复并进来写；其它 PR 即使同日合入也单列。
- **PR 链接**：涉及 PR、引入 PR、非业务表里的编号都写成 `[#n](html_url)`，不要只写 `#n`。优先用 API 的 `html_url`；没有则 `https://gitcode.com/{owner}/{repo}/merge_requests/{n}`。
- **合入分支**：该 PR 的 `base`（通常是 master）。有用户指定的对照分支才追加时差。

意见原则与 `gitcode-review` 相同：先读实现再下结论；新增文件先定职责再定归属（目标目录可以尚不存在）；只写能帮后续修改的风险，不写空泛「该不该」。

## 输出模板

```markdown
# {owner}/{repo} master 合入回顾（{from} ~ {to}）

## 范围
- 仓 / 本地路径 / 基准分支
- PR 筛选（含路径前缀：写明只看哪些目录）
- 对照分支：未指定则写「未指定」，不要补扫其它分支
- 数据来源（API / 仅 git log）

## 修改点

### 1. {主题名}
- 涉及 PR：[#{n}]({html_url})（{merged_at} 合入 {base}）… ；[#{m}]({html_url}) 修复 [#{n}]({html_url}) …
- 引入：[#{x}]({html_url}) 于 {date} 合入 {base}（窗外也写在这里）
- 描述 vs 代码：…（含夹带）
- 做法：…
- 风险 / 遗漏：…
- 合入分支：{base} {date}

## 非业务合入（docs / CI，可选）
一句话带过。
```

用户点名对照分支时，才在范围里写该分支，并在各修改点「合入分支」追加「{对照} {date}（差 N 天）/ 尚未合入」。不要单开「本周合入 vs 版本分支」总表去扫用户没点的分支。

## 负向案例

本 skill 在 msprof 2026-09-05～12 回顾里出过的错，写报告前对照一遍：

1. **根因与修复拆开**。把 Python `all_file.complete`、wait_flag 旧口径等写到文末「窗口外根因」表，读者看不到这笔修复对应的是哪天引入的问题。根因编号和合入日必须写在该修改点的「引入」字段。
2. **把不相关的合入捏成一条**。#487（统一 DB：DPUTask `globalTid` / PMU `timestampNs`）与 #497（AICPU CSV 补 `deviceId`、时间列加 `\t`）只是同秒合入 master，文件无交集、方法也不相关，不能写成「统一 DB / AICPU 导出」。同日、同作者、同属 C 化都不是「相关代码」。
3. **去找实际没合入的分支**。用户未点名对照分支时，仍 fetch/contains 了 `26.0.0`、`26.1.0`、`br_26.0.0_beta1` 并写「尚未合入」。合入分支只报 PR 的 `base`（该周即 master）。
4. **只信描述、漏报夹带**。#503 描述是 sqlite `DT_NEEDED` 改成 `libsqlite3.so.0`，diff 还改了 `.vscode/tasks.json` 的 Build 命令。首稿只写 sqlite。描述没提的 diff 必须写进「描述 vs 代码」。
5. **涉及 PR 只有编号没有链接**。mspti 2026-08-13～09-12 回顾首稿写成 `#164（合入 master）`。必须用 `[#164](https://gitcode.com/Ascend/mspti/merge_requests/164)`。引入 PR、非业务表里的 PR 同样带链接。

## 约束

- 分析基准永远是 **当时已在 master 上的树**（当前 `origin/master` 即可，因窗口内 PR 已合入）。
- 不要 checkout 到用户开发仓 `E:\Code\msprof`。
- 不要把回顾 md 提交进业务仓。
- 不要用开 PR 的行内评论接口发这些结论。
