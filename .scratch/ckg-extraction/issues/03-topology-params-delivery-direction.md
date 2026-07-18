# 03 — 拓扑参数 + 讲授走向

Status: done

## What to build

计算并展示 CKG 的拓扑参数与讲授走向。

- 新增**有向图**拓扑计算（不复用现有无向树版）：
  - `depth` = 源点（入度 0）到汇点（出度 0）的最长有向路径
  - `branch_factor` = 非汇点的平均出度
  - `convergence_count` = 入度 > 1 的节点数（DAG 区别于树的关键）
  - `density`、`avg_path_length`
  - `clustering`（在无向投影上算，二级观测 —— 先算后筛，可能在本数据上恒 0）
- 计算 `bottomup_ratio`（讲授走向）：沿每条先修边 A→B 比较 `first_para`，"先讲前置 A"的边占比；引入位置相同的边不计入分子分母。
- 参数存入 `course_ckg`，并在中间面板「结果区」显示。

术语「讲授走向 / 自底向上比例」见 CONTEXT.md；依据 ADR 0003。

## Acceptance criteria

- [ ] 新增有向图拓扑函数，算出 `depth` / `branch_factor` / `convergence_count` / `density` / `avg_path_length` / `clustering`
- [ ] `bottomup_ratio` 按定义计算（同 `first_para` 的边排除在外）
- [ ] 上述参数持久化到 `course_ckg`
- [ ] 中间面板结果区展示这组参数
- [ ] `clustering` 照算且不阻断流程；若在本数据上恒为 0，UI 如实呈现（不伪装有区分力）

## Blocked by

- 02-prerequisite-edges-dag-view

## Comments

- **2026-06-25 14:32** — 自动开发完成。实现要点：新增有向图 `compute_dag_topology` + `compute_bottomup_ratio`，init_db 用 PRAGMA table_info 幂等加列，worker 计算并持久化、API 返回、中间面板新增结果区（三语 i18n，clustering/bottomup 诚实显示）。
