---
name: codebase-slop-audit
description: >
  Run a codebase-wide slop audit and, only when asked, clean up the accepted
  candidates. Finds useless tests, unnecessary wrappers, dead code, and
  redundant abstractions by reading files and tracing real call paths.
  Layout, finder, and adversarial review each run in a fresh session of the
  same model that is executing this skill, at that model's highest reasoning
  effort. The parent audits the surviving targets and writes a ranked plan.
  Zero findings is a valid result. Use when the user asks for a slop audit,
  dead-code or redundancy sweep, 全库清理, 无用测试, 冗余抽象, or
  /codebase-slop-audit. Also use when they ask to clean up that plan with a
  fresh swarm and then verify.
---

# 全库冗余清理

父会话是编排者，自己不做扫库。蜂群成员都是新会话，提示词自包含。不要恢复查找、复查、修改或验证会话，也不要把一个成员的记录交给下一个。

## 输入

- 仓库：用户点名的工作区，否则用当前工作区。
- 检查目标：无用测试、多余包装、死代码、重复抽象。用户换了检查目标，就换目标，流程不变。
- 模型：正在执行本 skill 的模型。蜂群用同一个模型。不要问用户选模型，也不要换成别的模型。
- 强度：这个模型所支持的最高推理强度。每个蜂群成员都设上。不要留默认值，也不要照抄编排者此刻的强度。模型没有强度档位就不设。

## 两段停

1. 审计只读，交一份排序后的清理计划，不改仓库。
2. 只有用户要求清掉候选，或同一次请求写明先审计再清理，才进入清理。先写完计划，再改计划留下的项。

## 怎么发现代码

只能列目录和通读文件。不要搜索文件内容，不要用符号索引、tags 或语言服务的引用查询。成员若只抽样、只报搜索命中、或留下未读文件，这一块就不算做完，拆开重跑。

没有调用方，靠读完这块范围来证明，不靠一次空搜索。导出符号的调用方可能在块外：记下来，交给后面的块或编排者去读那些文件。

## 占满槽位

覆盖账本没关之前，保持有成员在跑。

原生子会话只有在「同一模型 + 该模型最高强度」时才算数。开不了这个强度，或者并发上限满了被拒绝或排队，就改开一个新的 CLI 进程。能开 CLI 就不要干等槽位。

每个成员一个新进程，不恢复已有会话。模型传正在执行本 skill 的那个，强度传它的最高档。

当前 Agent 是 Grok 时：

```bash
grok --cwd <abs-repo> -m <model> --effort <highest-for-that-model> --prompt-file <tmp-prompt> --output-format json --tools read_file,list_dir
```

其它 Agent 用它自己的一次性会话入口，模型和最高强度同样传进去。提示词文件写在仓库外，成员返回后删掉。审计和复查只用上面的只读工具。清理和验证用正常工具集。无人值守的清理或验证会话不能卡在权限确认上，沿用本会话已经有的非交互批准。

每个成员的提示词写明仓库路径、检查目标、发现规则和这块的文件清单。查找返回主张。复查返回否掉的、留下的，以及它新加的。提示词里不要写「去看父会话」。

## 审计

### 分块

用新会话分头走互不重叠的顶层目录。每块小到一个查找者能通读其中每个文件。编排者合并，保证每个文件只进一块。账本出来之前不要开始查找。

### 先查找，再复查

每块一个新的查找会话。它返回后，空出的槽位立刻接下一份未读块的查找，同时为刚完成的块另开一个复查会话。复查是另一个会话：拿到文件清单和查找主张，自己重读，并试图否掉每条主张。

复查能指出真实调用方、测试确实守住的行为，或这层包装是唯一边界时，主张作废。留下的主张必须带双方读过的文件和追到的调用路径。复查新加的主张，编排者自己读过之前都算未核实。

### 编排者

幸存目标自己读，包括调用路径上的文件。读完不成立的删掉。被否掉的主张，只有自己按同样方式读过才能捡回来。这一步不要再丢给蜂群。

然后按优先级给出计划：

- 属于哪一类检查目标
- 路径和符号
- 追到的调用路径，或为了证明没有调用方而读过的文件
- 为什么算进检查目标
- 删掉会坏什么
- 以后要做的改动

读完但没有发现的块也列出来。空计划也是一次做完的审计，不要为了凑数加项。

## 覆盖账本

一次跑一份账本。一块关掉的条件是：文件清单和分块清单一致，查找和复查都读过每个文件。编排者记下自己读过的幸存目标。还有未读文件就再开一块。有未读文件就不能结束审计。

## 清理

沿用同样的新会话和槽位规则。每个修改者拿计划里的一项，或计划写明必须一起改的一组。修改者返回后，换一个新的验证会话重读改过的文件，并跑覆盖这些改动的测试。

验证还报的问题由编排者在父会话里修。不要再丢给另一群。

用户没要求就不要提交或推送。
