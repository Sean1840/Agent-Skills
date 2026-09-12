# CANN / Profiling skills

分析 msprof、torch_npu profiler、plog。入口是 **cann-prof-pipeline**，不要一上来就 parse/collect。

## 技能

| Skill | 何时用 |
|---|---|
| `cann-prof-pipeline` | 分析这份数据/日志、口头报错（drv `ret=`） |
| `cann-prof-parse` | pipeline 判定解析，或明确是 timeline/csv/db 结果不对 |
| `cann-prof-collect` | pipeline 判定采集，或原始 PROF 缺文件 |
| `cann-log-locate` | 一行日志对到 path:line（底座） |
| `cann-log-triage` | 先盘点有哪些日志（底座） |

流程：`analysis-chain.md`（追到报错那条数据、pid 对齐）→ `version-and-fix.md`（改法、是否已合入、用户包版本）。

知识库：`docs/profiling/prior/`（流向，少改）与 `docs/profiling/details/`（文件名/宏，对不上就改）。

## 工具脚本

Python 包在 `tool/`（`cann_analyze` + `catalogs/`，含开箱 sqlite）。

```bash
cd E:\Code\Agent-Skills\cann\tool
set PYTHONPATH=.
python -m cann_analyze collect <path>
python -m cann_analyze evidence <path> -o evidence.json
python -m cann_analyze locate --line "<plog 一行>"
python -m cann_analyze status
```

或：`set CANN_ANALYZE_HOME=E:\Code\Agent-Skills\cann\tool` 后任意目录执行 `python -m cann_analyze`（`PYTHONPATH` 仍需包含 `tool/`）。

安装 skill：在 Agent-Skills 根目录 `python install.py`（Grok 已用 `config.toml` 的 paths 扫本仓）。
