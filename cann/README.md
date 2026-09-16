# CANN / Profiling skills

分析 msprof、torch_npu profiler、plog。入口是 **cann-prof-pipeline**，不要一上来就 parse/collect。

共享文档和 `cann_analyze` 工具放在 **`cann-prof-pipeline/references/`** 与 **`scripts/`**，这样 `npx skills add` 会随 pipeline 一起装上。其它 cann skill 用 `../cann-prof-pipeline/references/...` 引用（仓内与 npx 扁平安装后都成立，需同时装 pipeline）。

## 技能

| Skill | 何时用 |
|---|---|
| `cann-prof-pipeline` | 分析这份数据/日志、口头报错（drv `ret=`） |
| `cann-prof-parse` | pipeline 判定解析，或明确是 timeline/csv/db 结果不对 |
| `cann-prof-collect` | pipeline 判定采集，或原始 PROF 缺文件 |
| `cann-log-locate` | 一行日志对到 path:line（底座） |
| `cann-log-triage` | 先盘点有哪些日志（底座） |
| `cann-analyze-eval` | 评测 locate / 有效性，不用于现场诊断 |

流程：`references/analysis-chain.md` → `references/version-and-fix.md`。

知识库：`references/docs/profiling/prior/`（流向）与 `details/`（文件名/宏/表/连线）。统一 DB：[msprof-db.md](cann-prof-pipeline/references/docs/profiling/details/msprof-db.md)；timeline 连线：[timeline-flow.md](cann-prof-pipeline/references/docs/profiling/details/timeline-flow.md)。

## 工具脚本

```bash
set PYTHONPATH=<本仓>/cann/cann-prof-pipeline/scripts
python -m cann_analyze collect <path>
python -m cann_analyze evidence <path> -o evidence.json
python -m cann_analyze locate --line "<plog 一行>"
python -m cann_analyze status
```

安装：`npx skills add Sean1840/Agent-Skills -g -y --all`（见仓根 README）。cann 技能请一起装，至少包含 `cann-prof-pipeline`。
