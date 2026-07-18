# 03 — 新风格参数

Status: done

## What to build

在新结构(拆解树 + 讲述关联)上重算风格参数,收敛核心维度、移除共线的旧参数。

- **核心参数**(读拆解树骨架 + 讲述关联):
  - `decompose_depth` 拆解深度 = 拆解树高(往下拆几层)
  - `decompose_breadth` 拆解宽度 = 非叶节点平均子数(每个概念碎成几块)
  - `relation_density` 关联密度 = 讲述关联边数 / 概念数(横向连得多不多)
  - `convergence_count` 汇聚数 = 入度 > 1 的概念数(纯拆解树每点入度=1,>1 必来自讲述关联边)
- **辅助信号**(保留但不进核心):`bottomup_ratio` 引入走向 —— 沿**拆解边**比父子
  `first_para`,子概念先讲(先分后总)的边占比;同 `first_para` 的边不计。标注"辅助信号"。
- **移除**:`density` / `avg_path_length` / `clustering`(在拆解树+少量跨支边上与
  深度/宽度高度共线、无增量信息)。相关列与计算清理掉。
- 参数持久化到 `course_ckg`(幂等加列),中间面板结果区展示;辅助信号视觉上与核心区分。

术语/依据见 CONTEXT.md「CK 维度」、ADR 0003。

## Acceptance criteria

- [ ] 算出 `decompose_depth` / `decompose_breadth` / `relation_density` / `convergence_count`
- [ ] `bottomup_ratio` 按定义计算(沿拆解边、同 first_para 排除),标注为辅助信号
- [ ] 移除 `density`/`avg_path_length`/`clustering` 的计算与存储
- [ ] 参数幂等持久化到 `course_ckg`
- [ ] 中间面板结果区展示核心参数 + 辅助信号(视觉区分)
- [ ] 既有测试不回归;新增参数计算的单测

## Blocked by

- 02-grounded-relations

## Comments

- **2026-06-26 自动开发完成**。实现要点(TDD):
  - **核心参数**:`depth`=拆解深度、`branch_factor`=拆解宽度(复用 `compute_dag_topology` 在拆解边上算);新增 `compute_relation_density`(讲述关联边数/概念数)与 `compute_convergence_count`(在 **拆解边 + 讲述关联** 合并入度上算>1 的节点——纯拆解树恒 0,汇聚只来自关联);新增 `relation_density` 列(幂等迁移)。
  - **辅助信号**:`bottomup_ratio` 沿拆解边算,保留但 UI 标注"辅助、不进核心"。
  - **移除** density/avg_path_length/clustering:worker 不再计算,持久化为 NULL(列保留避免破坏性迁移);GET 响应、profile 聚合(`_aggregate_ckg_profile` 的 `param_keys`/SELECT)、前端结果面板均删除这三项;`compute_dag_topology` 函数本身不动(仍供 depth/breadth)。
  - **GET**:返回 `depth/branch_factor/convergence_count/relation_density/bottomup_ratio`,不再返回退役三项。
  - **前端**:结果面板核心 4 项(拆解深度/拆解宽度/关联密度/汇聚数)+ 辅助区(引入走向,虚线分隔);`renderCKGParams` 跟改;i18n 三语 relabel + 加 `param.relation_density`(retired 三键暂留,供 issue 04 待删的旧雷达引用)。
  - **测试**:新增 `compute_relation_density` / `compute_convergence_*`(含关联致汇聚、忽略未知/自环)单测;改写 worker 拓扑列断言(retired 三列=NULL、relation_density=0)、GET 参数契约(退役键不返回)、profile 聚合参数集、结果面板元素 + i18n 断言。CKG/参数/profile 相关 132 项全绿;全量 **249 passed / 22 failed**(22 均预存环境失败,无新增回归)。
  - 备注:知识图谱页的全库散点仍读 `depth`/`bottomup`(正常),retired 列返 NULL 无害;风格画像卡旧雷达(读 density 等)留待 issue 04 重构为三视图时一并替换。
