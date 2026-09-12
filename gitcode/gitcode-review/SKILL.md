---
name: gitcode-review
description: >
  Review a GitCode Pull Request against the local codebase (fetch the PR patch, do not
  review the diff in isolation), then post comments on specific diff lines via the GitCode API.
  Use when the user asks to 检视 GitCode PR、review GitCode merge request、给 PR 提行内意见、
  把检视意见发到 GitCode、or runs /gitcode-review. Not for GitHub/GitLab PRs.
---

# GitCode PR 行内检视

对 GitCode PR 做代码检视：先把 patch 落到本地仓、对照周边代码和全流程分析，再把意见挂到**改动文件的具体行**。禁止只盯 diff 文本下结论。

## 认证

环境变量 `GITCODE_API_TOKEN`（GitCode 个人访问令牌）。

- 没有 token：只在本地列出「文件 + 新文件行号 + 正文」，让用户自己去页面点行评论。
- 有 token：检视完成后，用户要求发到 GitCode 时再调用脚本发帖。
- 不要把 token 写进仓库或回显到聊天。

创建入口：GitCode 头像 → 个人设置 → 访问令牌。

## 工作流

1. 解析 PR URL 或 `owner/repo#number`（例：`https://gitcode.com/Ascend/msprof/pull/507` → owner=`Ascend` repo=`msprof` number=`507`）。
2. `GET /api/v5/repos/{owner}/{repo}/pulls/{number}` 取 `head.sha`、`head.ref`、`head.repo`、`base.sha`、`base.ref`、标题。
3. `GET /api/v5/repos/{owner}/{repo}/pulls/{number}/files?per_page=100` 得到**本 PR 改动文件清单**。`patch` 可能是 `{diff, new_path, ...}`。清单只用来限定审查范围，**不能当作审查材料本身**。
4. **把 patch 落到 `E:\Code\review\msprof` 再分析**（见下一节）。该目录是检视专用仓，不要用 `E:\Code\msprof`（开发仓）。fetch 失败时先说明缺口，不要用网页 diff 硬审完全程。
5. 对照周边代码和调用链确认问题后，再写意见。每条必须落到 **HEAD 新文件行号**（该行须出现在 diff 的 `+` 或上下文行上）。
6. 发帖用 `scripts/post_inline_comment.py`；发完立刻 `GET .../comments` 核对 `comment_type=diff_comment` 且 `diff_position.start_new_line` 等于传入行号。对不上就停，不要继续刷普通评论。
7. 若从未在当前环境验证过行内接口，先在一个小 PR 上发一条带标记的探测评论，确认 Files 页钉在目标行后，再发正式意见。

## 本地代码分析（必须做）

审查对象是「合入后的代码在本仓里怎么跑」，不是 patch 里那几行看起来像不像。

### 落到本地

msprof 检视**只**在 `E:\Code\review\msprof` 进行（专门拉 PR 代码，可随意 fetch/checkout）。不要动 `E:\Code\msprof`。

目录不存在或不是 git 仓时，先克隆：

```
git clone git@gitcode.com:Ascend/msprof.git E:\Code\review\msprof
```

拉 PR 并检出 head（本仓专用于 review，允许 checkout）：

```
cd E:\Code\review\msprof
git fetch origin <base.ref>
git fetch <head-repo-url> <head.ref>
git checkout --detach <head.sha>
git diff <base.sha> <head.sha> -- <changed files>
```

读全文用工作区文件或 `git show <head.sha>:<path>`。合入前版本：`git show <base.sha>:<path>`。

禁止：用 `E:\Code\msprof` 上过期的 `master` 去 diff 整个源分支。范围始终是 files API 那份清单。

### 对照仓内代码

对每个改动点至少做这些，做不到的写明「未核对」：

- **新增文件归属**：对 files API 里每个 **added** 文件，先读实现，用一句话说清它做什么（采集驱动、校验、C 解析、实体、导出、ST 编排等），再对照 `docs/en/dir_structure.md` 和现有树，给出**明确归属**。落点可以是已有目录，也可以是**尚不存在、但按架构应当新建的路径/文件**（例如还没有 `test/st/scenarios/` 或 `domain/xxx/` 时，仍应建议新建并说明职责）。现有树缺层不等于「无处可放」或省略建议。禁止只问「该不该放这里」。意见必须带搬迁/拆分/改名/新建的落点，钉在该文件第 1 行或模块说明处。
- **调用方**：谁调用新/改函数；import、export、collection、C processor、UT 是否都接到同一条链。
- **同类实现**：仓里已有的邻近模块（同类 processor、PathManager、常量、清目录逻辑）怎么做；本 PR 是否另起一套。
- **数据流**：入口 → 落盘/内存 → 计算 → 导出/统一 DB。缺环、静默空表、只在 export 生成、import 看不到，都要写进意见。
- **失败与脏数据**：文件不存在、Query 失败、主键冲突、clear 残留、递归扫目录。
- **测试**：生产路径有、UT 只覆盖快乐路径的，点名缺的分支。

意见必须能指出「对照了哪处现有代码」得出的结论。只复述 patch 文本、没有调用链或同类对比的，不算完成检视。

## 发帖契约（唯一正确参数）

`POST https://api.gitcode.com/api/v5/repos/{owner}/{repo}/pulls/{number}/comments`

JSON：

```json
{
  "body": "[review]【设计】标题\n\n- 问题：...\n- 修复：...\n- 示例：...",
  "path": "analysis/foo.py",
  "position": 417,
  "commit_id": "<head sha>"
}
```

- `path`：仓库内相对路径，与 files API 的 `filename` 一致。
- `position`：**新文件行号**（1-based），不是 GitHub 那种 unified-diff 位移。
- `commit_id`：PR `head.sha`。
- Header：`Authorization: Bearer $GITCODE_API_TOKEN` 与 `PRIVATE-TOKEN: $GITCODE_API_TOKEN`。

**禁止用 `line`。** GitCode 收到 `line` 会当成讨论区 `pr_comment`，Files 页看不到。

成功标志（GET 同一 comments 列表）：

```json
{
  "comment_type": "diff_comment",
  "diff_position": {
    "position_type": "text",
    "start_new_line": 417,
    "end_new_line": 417
  }
}
```

删除误发：`DELETE /api/v5/repos/{owner}/{repo}/pulls/comments/{numeric_id}`（用 GET 列表里的数字 `id`，不是 POST 返回的 hash）。

## 意见格式

每条正文必须用这个结构（便于作者改、也便于统计检视密度）：

```
[review]【维度】一句话标题

- 问题：现在这样会怎样（后果，不要空泛）。
- 修复：作者该怎么改（路径/接口/逻辑的落点，不要只提疑问）。
- 示例：
```code```
```

维度用一个：设计 / 规范 / 复用 / 安全 / 性能 / 可读性 / 测试。

只发能帮作者改代码的意见：必须有可执行的修复或明确思路（改哪、改成什么样）。只抛问题、只问「该不该」、没有落点的，不要发。风格吹毛求疵、与本 PR 无关的历史代码不要发。

## 检视切入

- **设计**：数据流、职责边界、新增文件的实现职责与架构分层是否对齐（先定作用再定归属）。
- **复用**：是否该用已有 PathManager / 常量 / processor 模式，而不是再写一套。
- **安全**：路径遍历深度、SQL 拼接、主键冲突、脏文件残留。
- **性能**：无界递归、按行循环本可用批量/双指针的算法。
- **测试**：生产路径有、UT 没有的分支。
- **规范**：魔法数字、命名、日志。

## 脚本

从本 skill 目录调用：

```
python <this-skill>/scripts/post_inline_comment.py \
  --owner Ascend --repo msprof --pr 241 \
  --path analysis/common_func/constant.py \
  --position 417 \
  --commit-id <head_sha> \
  --body-file comment.md
```

`--verify` 发完会 GET 并检查 `diff_comment` 行号。失败则非 0 退出。
